import socket
import struct
import sys
import concurrent.futures
from os import environ


def send_image(filename):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("127.0.0.1", 33007))

        # Envia o tamanho do nome do arquivo
        filename_bytes = filename.encode()
        filename_len = struct.pack(">I", len(filename_bytes))
        client_socket.sendall(filename_len)

        # Envia o nome do arquivo
        client_socket.sendall(filename_bytes)

        # Envia o arquivo
        with open(filename, "rb") as f:
            while chunk := f.read(8192):  # Lê em blocos maiores
                client_socket.sendall(chunk)

        print(f"Imagem {filename} enviada")

    except Exception as e:
        print(f"Erro ao enviar o arquivo: {e}")

    finally:
        client_socket.close()


if __name__ == "__main__":
    objects_to_backup = sys.argv[1:]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(send_image, objects_to_backup))
