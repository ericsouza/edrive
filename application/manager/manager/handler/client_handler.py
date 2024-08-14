import db
import service
import socket
import logging

def get_workers_selection(connection: socket.socket, filename: str):            
    stored_object = db.get_object_by(filename)
    # se o arquivo já existe e estamos recebendo uma nova copia
    # então, na realidade temos uma atualização e precisamos forçar que
    # essa atualização seja feita nos servidores onde o objeto já existe.
    # o parametro include serve justamente pra forçarmos os servidores
    include = stored_object.workers if stored_object else []
    logging.warn(f"DEBUG 1: {[x.host for x in include]}")
    primary_worker = service.select_worker(include=include)
    secondary_worker = service.select_worker(exclude=[primary_worker], include=include)
    response = f"{primary_worker.key}::{secondary_worker.key}"
    logging.warn(f"DEBUG 2: {response}")
    connection.sendall(response.encode())

router = {
    "bk": get_workers_selection # bk -> backup object
}

def handle_client(connection):
    try:
        # Recebe o tamanho do nome do arquivo
        command, filename = connection.recv(1024).decode().split("::")
        router[command](connection, filename)
    except Exception as e:
        logging.error(f"Erro ao selecionar os workers: {e}", e)

    finally:
        connection.close()
