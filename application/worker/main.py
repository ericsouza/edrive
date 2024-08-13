import threading
import socket
import struct
from os import environ
from time import sleep
import logging
from pathlib import Path
import shutil

deployment_mode = environ.get("DEPLOYMENT_MODE", "local")

MANAGER_HOST = environ.get("MANAGER_HOST", "127.0.0.1")
HOST_TO_SERVE = "0.0.0.0"
WORKER_PUBLIC_HOST = socket.gethostname()
worker_port = 31000


FILES_FOLDER_NAME = "./files"
if deployment_mode == "local":
    worker_port = int(environ.get("EDRIVE_WORKER_PORT"))
    HOST_TO_SERVE = "127.0.0.1"
    WORKER_PUBLIC_HOST = "127.0.0.1"
    FILES_FOLDER_NAME = f"./files-{worker_port}"

shutil.rmtree(FILES_FOLDER_NAME, ignore_errors=True)
Path(FILES_FOLDER_NAME).mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)


class ConnectionToManagerRefused(Exception): ...


def copy_object_to_worker(filename: str, whost, wport):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((whost, wport))

        # envia o tipo de comando
        client_socket.sendall("up".encode())

        # Envia o tamanho do nome do arquivo
        filename_bytes = filename.encode()
        filename_len = struct.pack(">I", len(filename_bytes))
        client_socket.sendall(filename_len)

        # Envia o nome do arquivo
        client_socket.sendall(filename_bytes)
        # Envia o arquivo
        with open(f"{FILES_FOLDER_NAME}/{filename}", "rb") as f:
            while chunk := f.read(8192):  # Lê em blocos maiores
                client_socket.sendall(chunk)

    except Exception as e:
        print(f"Erro ao copiar o arquivo {filename}. Erro: {e}")

    finally:
        client_socket.close()


def upload_handler(connection: socket.socket, filename: str):
    # Abre um arquivo para escrita
    with open(f"{FILES_FOLDER_NAME}/{filename}", "wb") as f:
        while True:
            data = connection.recv(8192)  # Lê em blocos maiores
            if not data:
                break
            f.write(data)
    print(f"Imagem salva como {filename}")


def copy_object_handler(connection: socket.socket, filename: str):
    new_worker = connection.recv(1024).decode()
    new_worker_host, new_worker_port = new_worker.split(":")
    logging.info(f"Copiando arquivo {filename} para {new_worker}")
    print(f"Copiando arquivo {filename} para {new_worker}")
    copy_object_to_worker(filename, new_worker_host, int(new_worker_port))


router = {"up": upload_handler, "cp": copy_object_handler}


def handle_client(connection: socket.socket):
    try:
        # Available commands: up,cp,de,dl
        # Onde:
        #   up -> upload (indica que um object deve ser salva no servidor)
        #   cp -> copy (indica que um object deve ser copiada para outro servidor)
        #   de -> delete (indica que um object deve ser apagada)
        #   dl -> download (indica que um object foi requisitado para download)

        # Recebe o tamanho do nome do arquivo
        command = connection.recv(2).decode()
        raw_msglen = connection.recv(4)
        if not raw_msglen:
            return
        msglen = struct.unpack(">I", raw_msglen)[0]

        # Recebe o nome do arquivo
        filename = connection.recv(msglen).decode().strip()

        logging.info(f"Received {command} for {filename}")

        # repassa para o handler adequado
        router[command](connection, filename)

    except Exception as e:
        logging.error(f"Erro ao salvar o arquivo: {e}")

    finally:
        connection.close()


def _run_worker(worker_port: int = worker_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST_TO_SERVE, worker_port))
        s.listen()

        logging.info(f"Servidor escutando em {HOST_TO_SERVE}:{worker_port}")
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
            manager_address = (MANAGER_HOST, 37127)

            client_socket.connect(manager_address)

            # Enviar dados
            message = f"connect:{WORKER_PUBLIC_HOST}:{worker_port}"
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
    print("Iniciando worker")
    start()
