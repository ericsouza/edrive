from redis import Redis
from rq import Queue, Connection, Worker

# Conexão com o Redis
_redis_conn = Redis()
_queue = Queue(name="image_processor_queue", connection=_redis_conn)


def enqueue_image(filename):
    _queue.enqueue(_process_filename, filename)


def _process_filename(filename):
    print(f"Processando arquivo: {filename}")


def start():
    # Executa o worker para processar a fila
    with Connection(_redis_conn):
        worker = Worker([_queue])
        worker.work()
