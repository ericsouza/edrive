import socket
import struct
import sys
import concurrent.futures
from os import environ, stat
import logging

logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.INFO
)

def send_copy_command(
    filename: str, file_size: int, from_worker: str, to_worker: str
):
    try:
        from_worker_host, from_worker_port = from_worker.split(":")
        to_worker_host, to_worker_port = to_worker.split(":")

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((from_worker_host, int(from_worker_port)))

        # envia o tipo de comando
        client_socket.sendall("cp".encode())

        # Envia o tamanho do nome do arquivo
        filename_bytes = filename.encode()
        filename_len = struct.pack(">I", len(filename_bytes))
        client_socket.sendall(filename_len)

        # Envia o nome do arquivo
        client_socket.sendall(filename_bytes)
        # Envia o novo worker para salvar uma copia
        client_socket.sendall(f"{to_worker_host}:{to_worker_port}".encode())
        logging.info(
            f"Cópia de {from_worker_host}:{from_worker_port} do objeto {filename} enviada para {to_worker_host}:{to_worker_port}"
        )

    except Exception as e:
        logging.error(
            f"Erro ao copiar de {from_worker_host}:{from_worker_port} o objeto {filename} para {to_worker_host}:{to_worker_port}. Erro: ",
            e,
        )
    finally:
        client_socket.close()


def send_image(filename, workers: list[str]):
    try:
        primary_host, primary_port = workers[0].split(":")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((primary_host, int(primary_port)))

        # enviamos o comando de upload pro worker
        client_socket.sendall("up".encode())
        # Envia o tamanho do nome do arquivo. Serializamos usando
        # o unsigned int da linguagem C para garantir que vai ocupar exatamente 4 bytes
        filename_bytes = filename.encode()
        filename_len = struct.pack(">I", len(filename_bytes))
        client_socket.sendall(filename_len)

        # Envia o nome do arquivo
        client_socket.sendall(filename_bytes)

        # Envia o arquivo em chunks
        with open(filename, "rb") as f:
            while chunk := f.read(8192):  # Lê em blocos maiores
                client_socket.sendall(chunk)
        file_size = stat(filename).st_size
        
        ## ENVIAMOS O COMANDO PARA O WORKER PRIMÁRIO MANDAR A IMAGEM PRO SECUNDARIO
        send_copy_command(filename, file_size, workers[0], workers[1])
        
        logging.info(f"Imagem {filename} salva")

    except Exception as e:
        logging.error(f"Erro ao enviar o arquivo: {e}")

    finally:
        client_socket.close()


def backup_image(filename: str):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    manager_address = ("127.0.0.1", 33007)
    client_socket.connect(manager_address)
    message = f"bk::{filename}"
    client_socket.sendall(message.encode())
    response = client_socket.recv(1024).decode()
    client_socket.close()
    workers = response.split("::")
    send_image(filename, workers)


if __name__ == "__main__":
    objects_to_backup = sys.argv[1:]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(backup_image, objects_to_backup))
