import socket
import threading

from handler.worker_handler import handle_worker
from handler.client_handler import handle_client


def _run_manager_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 37127))
    server.listen(5)
    print("Servidor de controle rodando em 127.0.0.1:37127")

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
    server.bind(("127.0.0.1", 33007))
    server.listen(5)
    print("Servidor escutando em 127.0.0.1:33007")

    while True:
        client_socket, addr = server.accept()
        print(f"Conexão estabelecida com {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()


def start():
    server_thread = threading.Thread(target=_run_server, daemon=True)
    manager_server_thread = threading.Thread(target=_run_manager_server, daemon=True)
    server_thread.start()
    manager_server_thread.start()
