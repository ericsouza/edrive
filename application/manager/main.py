import socket
import threading

def handle_client(client_socket):
    try:
        # Recebe o nome do arquivo
        filename = client_socket.recv(100).decode().strip()

        # Abre um arquivo para escrita
        with open(filename, 'wb') as f:
            while True:
                data = client_socket.recv(8192)  # Lê em blocos maiores
                if not data:
                    break
                f.write(data)

        print(f"Imagem salva como {filename}")

    except Exception as e:
        print(f"Erro ao salvar o arquivo: {e}")

    finally:
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', 8888))
    server.listen(5)
    print('Servidor escutando em 127.0.0.1:8888')

    while True:
        client_socket, addr = server.accept()
        print(f'Conexão estabelecida com {addr}')
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    main()
