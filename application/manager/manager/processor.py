import struct
import socket
from redis import Redis
from rq import Queue, Connection
from rq import Worker as RqWorker
import db
import os
from db import Worker
from  os import environ
import service
import logging

REDIS_HOST = environ.get("REDIS_HOST", "127.0.0.1")

def send_image(filename, worker: Worker) -> int:
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((worker.host, worker.port))

        # envia o tipo de comando
        client_socket.sendall("up".encode())

        # Envia o tamanho do nome do arquivo
        filename_bytes = filename.encode()
        filename_len = struct.pack(">I", len(filename_bytes))
        client_socket.sendall(filename_len)

        # Envia o nome do arquivo
        client_socket.sendall(filename_bytes)
        # Envia o arquivo
        with open(f"files/{filename}", "rb") as f:
            while chunk := f.read(8192):  # Lê em blocos maiores
                client_socket.sendall(chunk)
        file_size = os.stat(f"files/{filename}").st_size
        db.add_object_to_worker(worker, filename, file_size)
        logging.info(f"Imagem {filename} enviada para: {worker.key}")
        return file_size
    except Exception as e:
        logging.error(f"Erro ao enviar o arquivo: {e}", e)

    finally:
        client_socket.close()


# Conexão com o Redis
_redis_conn = Redis(host=REDIS_HOST)
_queue = Queue(name="image_processor_queue", connection=_redis_conn)


def enqueue_image(filename):
    _queue.enqueue(_process_file, filename)


def _process_file(filename):
    logging.info(f"Processando arquivo: {filename}")
    stored_object = db.get_object_by(filename)
    # se o arquivo já existe e estamos recebendo uma nova copia
    # então, na realidade temos uma atualização e precisamos forçar que
    # essa atualização seja feita nos servidores onde o objeto já existe.
    # o parametro include serve justamente pra forçarmos os servidores
    include = stored_object.workers if stored_object else []
    primary_worker = service.select_worker(include=include)
    sent_file_size = send_image(
        filename=filename,
        worker=primary_worker,
    )
    secondary_worker = service.select_worker(exclude=[primary_worker], include=include)
    # envia copy command para que o primário mande o objeto pro secundário
    send_copy_command(
        filename,
        file_size=sent_file_size,
        from_worker=primary_worker,
        to_worker=secondary_worker,
    )
    # Remove do servidor principal após subir as 2 cópias para os workers
    os.remove(f"files/{filename}")
    db.add_object(filename, [primary_worker, secondary_worker])


def enqueue_worker_died(worker: Worker):
    _queue.enqueue(_process_dead_worker, worker)


def send_copy_command(
    filename: str, file_size: int, from_worker: Worker, to_worker: Worker
):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((from_worker.host, from_worker.port))

        # envia o tipo de comando
        client_socket.sendall("cp".encode())

        # Envia o tamanho do nome do arquivo
        filename_bytes = filename.encode()
        filename_len = struct.pack(">I", len(filename_bytes))
        client_socket.sendall(filename_len)

        # Envia o nome do arquivo
        client_socket.sendall(filename_bytes)
        # Envia o novo worker a salvar uma copia
        client_socket.sendall(to_worker.key.encode())
        db.add_object_to_worker(to_worker, filename, file_size)
        logging.info(
            f"Cópia de {from_worker.key} do objeto {filename} enviada para {to_worker.key}"
        )

    except Exception as e:
        logging.error(
            f"Erro ao copiar de {from_worker.key} o objeto {filename} para {to_worker.key}. Erro: ",
            e,
        )
    finally:
        client_socket.close()


def _process_dead_worker(dead_worker: Worker):
    files = [obj for obj in db.get_all_objects_by(dead_worker)]
    for file in files:
        filename, file_size = file.split(":")
        obj = db.get_object_by(filename)
        if obj:
            from_worker = [w for w in obj.workers if w != dead_worker][0]
            to_worker = service.select_worker(exclude=[dead_worker, from_worker])
            send_copy_command(filename, file_size, from_worker, to_worker)
            db.add_object(filename, [from_worker, to_worker])
    db.remove_worker(dead_worker, [fn.split(":")[0] for fn in files])


def start():
    # Executa o worker para processar a fila
    with Connection(_redis_conn):
        rq_worker = RqWorker([_queue])
        rq_worker.work()
