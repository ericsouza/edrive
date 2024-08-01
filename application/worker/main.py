import socket

# Criar um socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Conectar ao servidor
server_address = ('127.0.0.1', 37127)
client_socket.connect(server_address)

server_port=26739

try:
    # Enviar dados
    message = f'connect:127.0.0.1:{server_port}'
    client_socket.sendall(message.encode())

    # Receber resposta
    data = client_socket.recv(1024)
    print(f'Recebido: {data.decode()}')
finally:
    # Fechar a conexão
    client_socket.close()
