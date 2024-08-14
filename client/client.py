import socket
import struct
import sys
import concurrent.futures
from os import environ
import logging

logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.INFO
)

def send_image(filename, whost: str, wport: int):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((whost, wport))

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

        logging.info(f"Imagem {filename} enviada")

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
    for worker in workers:
        whost, wport = worker.split(":")
        send_image(filename, whost, int(wport))


if __name__ == "__main__":
    objects_to_backup = sys.argv[1:]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(backup_image, objects_to_backup))
