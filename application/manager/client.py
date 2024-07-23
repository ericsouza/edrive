import socket

def send_image(filename):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 33007))

        # Envia o nome do arquivo
        client_socket.send((filename + '\n').encode())

        # Envia o arquivo
        with open(filename, 'rb') as f:
            while chunk := f.read(8192):  # Lê em blocos maiores
                client_socket.send(chunk)

        print(f'Imagem {filename} enviada')

    except Exception as e:
        print(f"Erro ao enviar o arquivo: {e}")

    finally:
        client_socket.close()

if __name__ == "__main__":
    send_image('exemplo.jpg')
