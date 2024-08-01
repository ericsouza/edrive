import db


def handle_worker(connection, address):
    try:
        print(f"Conexão estabelecida com {address}")
        while True:
            data = connection.recv(1024)
            if not data:
                break
            payload: str = data.decode()
            command, whost, wip = payload.split(":")
            if command == "connect":
                print(f"Solicitação de conexão recebida: {whost}:{wip}")
                db.workers[f"{whost}:{wip}"] = {"status": "up"}
                connection.sendall("conexao estabelecida, bem vindo a rede".encode())
            elif command == "keepalive":
                print(f"Keep alive recebido de: {whost}:{wip}")
                connection.sendall("parabens por continuar vivo".encode())
            else:
                print("nada a ver oq tu mandou ai")
                connection.sendall("bad request".encode())
    except Exception as e:
        print(f"Erro ao lidar com worker {address}", e)

    finally:
        # Fechar a conexão
        connection.close()
