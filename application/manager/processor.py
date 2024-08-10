import struct
import socket
from redis import Redis
from rq import Queue, Connection, Worker
import random

servers = [
    {
        "id": 1,
        "host": "127.0.0.1",
        "port": 30001,
    },
    {
        "id": 2,
        "host": "127.0.0.1",
        "port": 30002,
    },
    {
        "id": 3,
        "host": "127.0.0.1",
        "port": 30003,
    },
]


def send_image(filename, server_id, server_host, server_port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_host, server_port))

        # Envia o tamanho do nome do arquivo
        name, extension = filename.split(".")
        filename = f"{name}-{server_id}.{extension}"
        filename_bytes = filename.encode()
        filename_len = struct.pack(">I", len(filename_bytes))
        client_socket.sendall(filename_len)

        # Envia o nome do arquivo
        client_socket.sendall(filename_bytes)

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
    selected_primary = select_server()
    send_image(
        filename=filename,
        server_id=selected_primary["id"],
        server_host=selected_primary["host"],
        server_port=selected_primary["port"],
    )
    selected_secondary = select_server(exclude_ids=[selected_primary["id"]])
    send_image(
        filename=filename,
        server_id=selected_secondary["id"],
        server_host=selected_secondary["host"],
        server_port=selected_secondary["port"],
    )


def select_server(exclude_ids: list[str] = []):
    available_servers = [sv for sv in servers if sv["id"] not in exclude_ids]
    return random.choice(available_servers)


def start():
    # Executa o worker para processar a fila
    with Connection(_redis_conn):
        worker = Worker([_queue])
        worker.work()
