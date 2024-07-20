from socket import socket, AF_INET, SOCK_STREAM

port = 33007
host = '' #localhost

socket_server = socket(AF_INET, SOCK_STREAM)

socket_server.bind((host, port))

socket_server.listen(1)

print("server up")

while True:
    conn_socket, addr = socket_server.accept()
    payload = conn_socket.recv(1024)
    conn_socket.send(payload.upper())
    conn_socket.close()
