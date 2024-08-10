import redis
from datetime import datetime, timedelta

WORKERS_LIST_KEY = "workers"

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


class WorkerAlreadyConnected(Exception): ...


class Worker:
    def __init__(self, host, port):
        self.host: str = host
        self.port: int = port
        self.key = f"{host}:{port}"

    @property
    def keepalive_key(self):
        return f"{self.key}:keepalive"

    def __str__(self) -> str:
        return f"<Worker host={self.host} port={self.port}>"

    def __repr__(self) -> str:
        return f"<Worker host={self.host} port={self.port}>"

    def __eq__(self, value: object) -> bool:
        return value.key == self.key

    @classmethod
    def from_db(cls, key: str):
        host, port = key.split(":")
        return Worker(host=host, port=int(port))


def add_worker(new_worker: Worker):
    workers = get_all_workers()
    if new_worker in workers:
        raise WorkerAlreadyConnected("Worker already in cluster")
    r.rpush(WORKERS_LIST_KEY, new_worker.key)


def get_all_workers() -> list[Worker]:
    try:
        all_workers = r.lrange(WORKERS_LIST_KEY, 0, -1)
        return [Worker.from_db(key) for key in all_workers]
    except Exception as e:
        return []


def remove_worker(worker: Worker):
    r.lrem(WORKERS_LIST_KEY, 1, worker.key)
    r.delete(worker.keepalive_key)

def mark_keepalive(worker: Worker) -> None:
    r.set(worker.keepalive_key, datetime.now().timestamp())

def get_keepalive(worker: Worker) -> bool:
    return r.get(worker.keepalive_key)
    
