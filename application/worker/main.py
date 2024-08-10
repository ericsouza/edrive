import threading
import socket
import struct
from os import getenv
from time import sleep
import logging

worker_port = int(getenv("EDRIVE_WORKER_PORT"))

logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)


class ConnectionToManagerRefused(Exception): ...


def handle_client(connection):
    try:
        # Recebe o tamanho do nome do arquivo
        raw_msglen = connection.recv(4)
        if not raw_msglen:
            return
        msglen = struct.unpack(">I", raw_msglen)[0]

        # Recebe o nome do arquivo
        filename = connection.recv(msglen).decode().strip()
        # Abre um arquivo para escrita
        with open(filename, "wb") as f:
            while True:
                data = connection.recv(8192)  # Lê em blocos maiores
                if not data:
                    break
                f.write(data)
        print(f"Imagem salva como {filename}")

    except Exception as e:
        logging.error(f"Erro ao salvar o arquivo: {e}")

    finally:
        connection.close()


def _run_worker(worker_port: int = worker_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", worker_port))
        s.listen()

        logging.info(f"Servidor escutando em 127.0.0.1:{worker_port}")
        while True:
            conn, addr = s.accept()
            logging.info(f"Conexão estabelecida com {addr}")
            client_handler = threading.Thread(target=handle_client, args=(conn,))
            client_handler.start()


def keepalive_updater():
    error_count = 0
    sleep(10)
    while True:
        try:
            connect(retries=0)
            if error_count >= 3:
                logging.info("connection to manager restablished")
            error_count = 0
        except Exception as e:
            error_count += 1
            logging.error("Failed to send keepalive to manager")
        if error_count >= 3:
            logging.critical(
                "Lost connection with manager after 3 attempts of keepalive"
            )
            sleep(30)
        else:
            sleep(12)


def connect(worker_port: int = worker_port, retries: int = 3):
    count = 0
    connected = False

    while count <= retries:
        try:
            # Criar um socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Conectar ao servidor
            manager_address = ("127.0.0.1", 37127)

            client_socket.connect(manager_address)

            # Enviar dados
            message = f"connect:127.0.0.1:{worker_port}"
            client_socket.sendall(message.encode())

            # Receber resposta
            data = client_socket.recv(1024)
            print(f"Recebido: {data.decode()}")

            # Fechar a conexão
            client_socket.close()
            connected = True
            break
        except ConnectionRefusedError:
            count += 1
            sleep(5)

    if not connected:
        logging.error("Cannot contact manager. Sorry :(")
        raise ConnectionToManagerRefused("Connection to manager lost.")


def start():
    port = connect()
    keepalive_updater_thread = threading.Thread(target=keepalive_updater, daemon=True)
    keepalive_updater_thread.start()
    _run_worker()


if __name__ == "__main__":
    start()
