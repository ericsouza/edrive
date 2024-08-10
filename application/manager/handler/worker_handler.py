import db
from db import Worker, WorkerAlreadyConnected


def handle_worker(connection, address):
    try:
        while True:
            data = connection.recv(1024)
            if not data:
                break
            payload: str = data.decode()
            command, whost, wport = payload.split(":")
            worker = Worker(whost, wport)
            if command == "connect":
                try:
                    db.add_worker(worker)
                    print(f"New {worker} connected to cluster")
                    current_workers = db.get_all_workers()
                    print(f"Currently there are {len(current_workers)} available workers: ", current_workers)
                    connection.sendall("connect:success".encode())
                except WorkerAlreadyConnected:
                    db.mark_keepalive(worker)
                    print("Received keep alive from", worker)
                    connection.sendall("keepalive:success".encode())
            else:
                connection.sendall("badrequest".encode())
    except Exception as e:
        print(f"Erro ao lidar com worker {address}", e)

    finally:
        # Fechar a conexão
        connection.close()
