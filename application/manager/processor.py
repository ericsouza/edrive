import struct
import socket
from redis import Redis
from rq import Queue, Connection
from rq import Worker as RqWorker
import random
import db
import os
from db import Worker


def send_image(filename, worker: Worker):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((worker.host, worker.port))

        # Envia o tamanho do nome do arquivo
        original_name = filename
        name, extension = filename.split(".")
        filename = f"{name}-{worker.port}.{extension}"
        filename_bytes = filename.encode()
        filename_len = struct.pack(">I", len(filename_bytes))
        client_socket.sendall(filename_len)

        # Envia o nome do arquivo
        client_socket.sendall(filename_bytes)
        # Envia o arquivo
        with open(f"files/{name}.{extension}", "rb") as f:
            while chunk := f.read(8192):  # Lê em blocos maiores
                client_socket.sendall(chunk)
        file_size = os.stat(f"files/{original_name}").st_size
        db.add_object_to_worker(worker, original_name, file_size)
        print(f"Imagem {original_name} enviada para: ", worker.key)

    except Exception as e:
        print(f"Erro ao enviar o arquivo: {e}")

    finally:
        client_socket.close()


# Conexão com o Redis
_redis_conn = Redis()
_queue = Queue(name="image_processor_queue", connection=_redis_conn)


def enqueue_image(filename):
    _queue.enqueue(_process_file, filename)


def _process_file(filename):
    print(f"Processando arquivo: {filename}")
    stored_object = db.get_object_by(filename)
    # se o arquivo já existe e estamos recebendo uma nova copia
    # então, na realide temos uma atualização e precisamos forçar que
    # essa atualização seja feita nos servidores onde o objeto já existe.
    # o parametro include serve justamente pra forçarmos os servidores
    include = stored_object.workers if stored_object else []
    primary_worker = select_worker(include=include)
    send_image(
        filename=filename,
        worker=primary_worker,
    )
    secondary_worker = select_worker(exclude=[primary_worker], include=include)
    send_image(
        filename=filename,
        worker=secondary_worker,
    )
    # Remove do servidor principal após subir as 2 cópias para os workers
    os.remove(f"files/{filename}")
    db.add_object(filename, [primary_worker, secondary_worker])


def select_worker(exclude: list[Worker] = [], include: list[Worker] = []):
    # primeiro vemos se foi passada uma lista "forçada" para salvar os arquivos
    forced_workers = list(set(include) - set(exclude))
    if forced_workers:
        return forced_workers[0]

    # senao, é pq o arquivo é novo no sistema e elegemos outro
    workers = db.get_all_workers()
    available_workers = [w for w in workers if w not in exclude]
    sorted_available_workers = sorted(available_workers, key=lambda w: w.used_storage)
    return sorted_available_workers[0]


def start():
    # Executa o worker para processar a fila
    with Connection(_redis_conn):
        rq_worker = RqWorker([_queue])
        rq_worker.work()
