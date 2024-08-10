import struct
import socket
from redis import Redis
from rq import Queue, Connection
from rq import Worker as RqWorker
import random
import db
from db import Worker


def send_image(filename, worker: Worker):
    try:
        print(f"types: {type(worker.host)}  --- {type(worker.port)}")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((worker.host, worker.port))

        # Envia o tamanho do nome do arquivo
        name, extension = filename.split(".")
        filename = f"{name}-{worker.port}.{extension}"
        filename_bytes = filename.encode()
        print("debug 1")
        filename_len = struct.pack(">I", len(filename_bytes))
        print("debug 2")
        client_socket.sendall(filename_len)

        # Envia o nome do arquivo
        print("debug 3")
        client_socket.sendall(filename_bytes)
        print("debug 4")
        # Envia o arquivo
        with open(f"files/{name}.{extension}", "rb") as f:
            while chunk := f.read(8192):  # Lê em blocos maiores
                client_socket.sendall(chunk)

        print(f"Imagem {filename} enviada")

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
    primary_worker = select_worker()
    send_image(
        filename=filename,
        worker=primary_worker,
    )
    secondary_worker = select_worker(exclude=[primary_worker])
    send_image(
        filename=filename,
        worker=secondary_worker,
    )


def select_worker(exclude: list[Worker] = []):
    workers = db.get_all_workers()
    available_workers = [w for w in workers if w not in exclude]
    return random.choice(available_workers)


def start():
    # Executa o worker para processar a fila
    with Connection(_redis_conn):
        rq_worker = RqWorker([_queue])
        rq_worker.work()
