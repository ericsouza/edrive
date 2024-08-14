import db
from db import Worker, WorkerAlreadyConnected
import logging

def handle_worker(connection, address):
    try:
        while True:
            data = connection.recv(1024)
            if not data:
                break
            payload: str = data.decode()
            command, wport = payload.split(":")
            if command == "connect":
                try:
                    worker = Worker(address[0], int(wport))
                    db.add_worker(worker)
                    logging.info(f"New {worker} connected to cluster")
                    db.mark_keepalive(worker)
                    current_workers = db.get_all_workers()
                    logging.info(
                        f"Currently there are {len(current_workers)} available workers: {current_workers}"
                    )
                    connection.sendall(address[0].encode())
                except WorkerAlreadyConnected:
                    worker = db.get_worker(host=address[0], port=int(wport))
                    db.mark_keepalive(worker)
                    connection.sendall("keepalive:success".encode())
            else:
                connection.sendall("badrequest".encode())
    except Exception as e:
        logging.error(f"Erro ao lidar com worker {address}", e)

    finally:
        # Fechar a conexão
        connection.close()
