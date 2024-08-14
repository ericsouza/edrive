import socket
import threading
from os import environ
import logging
from handler.worker_handler import handle_worker
from handler.client_handler import handle_client

deployment_mode = environ.get("DEPLOYMENT_MODE", "local")

HOST_TO_SERVE = "0.0.0.0"

if deployment_mode == "local":
    HOST_TO_SERVE = "127.0.0.1"

def _run_manager_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST_TO_SERVE, 37127))
    server.listen(5)
    logging.info(f"Servidor de controle rodando em {HOST_TO_SERVE}:37127")

    while True:
        client_socket, addr = server.accept()
        client_handler = threading.Thread(
            target=handle_worker,
            args=(
                client_socket,
                addr,
            ),
        )
        client_handler.start()


def _run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST_TO_SERVE, 33007))
    server.listen(5)
    logging.info(f"Servidor escutando em {HOST_TO_SERVE}:33007")

    while True:
        client_socket, addr = server.accept()
        logging.info(f"Conexão estabelecida com {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()


def start():
    server_thread = threading.Thread(target=_run_server, daemon=True)
    manager_server_thread = threading.Thread(target=_run_manager_server, daemon=True)
    server_thread.start()
    manager_server_thread.start()
