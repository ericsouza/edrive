import socket
import threading
from rq import Queue, Worker, Connection
from redis import Redis
import time

# Conexão com o Redis
redis_conn = Redis()
queue = Queue(connection=redis_conn)

def handle_client(client_socket):
    try:
        # Recebe o nome do arquivo
        filename = client_socket.recv(100).decode().strip()
        print("nome: ", filename)
        # Abre um arquivo para escrita
        with open(f"{filename.split(".")[0]}-out.jpg", 'wb') as f:
            while True:
                data = client_socket.recv(8192)  # Lê em blocos maiores
                if not data:
                    break
                f.write(data)

        print(f"Imagem salva como {filename}")
        
        # Envia o nome do arquivo para a fila
        queue.enqueue('process_image', filename)

    except Exception as e:
        print(f"Erro ao salvar o arquivo: {e}")

    finally:
        client_socket.close()

def process_image(filename):
    print(f"Processando arquivo: {filename}")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', 33007))
    server.listen(5)
    print('Servidor escutando em 127.0.0.1:33007')

    while True:
        client_socket, addr = server.accept()
        print(f'Conexão estabelecida com {addr}')
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    # Executa o servidor em um thread separado
    server_thread = threading.Thread(target=main)
    server_thread.start()
    
    # Executa o worker para processar a fila
    with Connection(redis_conn):
        worker = Worker([queue])
        worker.work()
