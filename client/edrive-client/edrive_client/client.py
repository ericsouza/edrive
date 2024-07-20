from socket import socket, AF_INET, SOCK_STREAM

class Client:
    def __init__(self, host: str, port: int = 33007):
        self.socket_client = socket(AF_INET, SOCK_STREAM)
        self.host = host
        self.port = port

    def save_image(self, image_path: str):
        self.socket_client.connect((self.host, self.port))
        self.socket_client.send(image_path.encode())
        response = self.socket_client.recv(1024)
        print("from server: ", response.decode())
        self.socket_client.close()

