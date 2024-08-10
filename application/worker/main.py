import threading
import socket
import struct
from os import getenv


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
        print(f"Erro ao salvar o arquivo: {e}")

    finally:
        connection.close()

def _run_worker(worker_port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", worker_port))
        s.listen()

        print(f"Servidor escutando em 127.0.0.1:{worker_port}")
        while True: 
            conn, addr = s.accept()
            print(f"Conexão estabelecida com {addr}")
            client_handler = threading.Thread(target=handle_client, args=(conn,))
            client_handler.start()

def connect(worker_port: int):
    # Criar um socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Conectar ao servidor
    manager_address = ("127.0.0.1", 37127)
    client_socket.connect(manager_address)

    try:
        # Enviar dados
        message = f"connect:127.0.0.1:{worker_port}"
        client_socket.sendall(message.encode())

        # Receber resposta
        data = client_socket.recv(1024)
        print(f"Recebido: {data.decode()}")
    finally:
        # Fechar a conexão
        client_socket.close()

def start():
    worker_port = int(getenv("EDRIVE_WORKER_PORT"))
    port = connect(worker_port=worker_port)
    _run_worker(worker_port=worker_port)


if __name__ == "__main__":
    start()
