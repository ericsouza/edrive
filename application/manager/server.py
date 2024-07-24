import socket
import threading

import struct
from processor import enqueue_image


def handle_client(client_socket):
    try:
        # Recebe o tamanho do nome do arquivo
        raw_msglen = client_socket.recv(4)
        if not raw_msglen:
            return
        msglen = struct.unpack(">I", raw_msglen)[0]

        # Recebe o nome do arquivo
        filename = client_socket.recv(msglen).decode().strip().split(".")[0]

        # Abre um arquivo para escrita
        with open(f"{filename}-out.jpg", "wb") as f:
            while True:
                data = client_socket.recv(8192)  # Lê em blocos maiores
                if not data:
                    break
                f.write(data)

        print(f"Imagem salva como {filename}")

        # Envia o nome do arquivo para a fila
        enqueue_image(filename)

    except Exception as e:
        print(f"Erro ao salvar o arquivo: {e}")

    finally:
        client_socket.close()


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


def start_server():
    server_thread = threading.Thread(target=_run_server)
    server_thread.start()
