import redis
from datetime import datetime, timedelta

WORKERS_LIST_KEY = "workers"

_r = redis.Redis(host="localhost", port=6379, decode_responses=True)


class WorkerAlreadyConnected(Exception): ...


class Worker:
    def __init__(self, host, port, used_storage: int = 0):
        self.host: str = host
        self.port: int = port
        self.key: str = f"{host}:{port}"
        self.used_storage: int = used_storage

    @property
    def keepalive_key(self):
        return f"{self.key}:keepalive"

    @property
    def objects_key(self):
        return f"{self.key}:objects"

    @property
    def used_storage_key(self):
        return f"{self.key}:storage"

    def __str__(self) -> str:
        return f"<Worker host={self.host}, port={self.port}, used_storage={self.used_storage}>"

    def __repr__(self) -> str:
        return f"<Worker host={self.host}, port={self.port}, used_storage={self.used_storage}>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Worker):
            return other.key == self.key
        return False

    def __hash__(self) -> int:
        return hash(self.key)

    @classmethod
    def from_db(cls, key: str, used_storage: int = 0):
        host, port = key.split(":")
        return Worker(host=host, port=int(port), used_storage=used_storage)


class StoredObject:
    def __init__(self, filename, workers: list[Worker]):
        self.filename = filename
        self.workers = workers

    @classmethod
    def from_db(cls, filename, stored_info: str):
        workers = [Worker.from_db(w) for w in stored_info.split("::")]
        return StoredObject(filename, workers)


def add_worker(new_worker: Worker):
    workers = get_all_workers()
    if new_worker in workers:
        raise WorkerAlreadyConnected("Worker already in cluster")
    _r.rpush(WORKERS_LIST_KEY, new_worker.key)


def get_worker(host: str, port: int):
    worker = [w for w in get_all_workers() if w.host == host and int(w.port) == port]
    if worker:
        return worker[0]


def get_all_workers() -> list[Worker]:
    all_workers = _r.lrange(WORKERS_LIST_KEY, 0, -1)
    workers = []
    for worker in all_workers:
        used_storage = get_used_storage_by(worker_identity=worker)
        workers.append(Worker.from_db(key=worker, used_storage=used_storage))
    return workers


def remove_worker(worker: Worker, filenames):
    for filename in filenames:
        remove_worker_from_object(filename, worker)
    _r.delete(worker.keepalive_key)
    _r.delete(worker.objects_key)
    _r.delete(worker.used_storage_key)
    _r.lrem(WORKERS_LIST_KEY, 1, worker.key)


def mark_keepalive(worker: Worker) -> None:
    _r.set(worker.keepalive_key, datetime.now().timestamp())


def get_keepalive(worker: Worker) -> bool:
    return _r.get(worker.keepalive_key)


def add_object_to_worker(worker: Worker, filename: str, file_size: int):
    objects_in_worker = get_all_objects_by(worker)

    already_present_object = None
    for obj in objects_in_worker:
        if obj.split(":")[0] == filename:
            already_present_object = obj
            break
    if already_present_object:
        old_size = already_present_object.split(":")[1]
        remove_object_by(worker, filename, old_size)

    _r.rpush(worker.objects_key, f"{filename}:{file_size}")
    _r.incr(worker.used_storage_key, amount=file_size)


def remove_object_by(worker: Worker, filename, file_size):
    _r.lrem(worker.objects_key, 1, f"{filename}:{file_size}")
    _r.decr(worker.used_storage_key, file_size)


def get_all_objects_by(worker: Worker):
    return _r.lrange(worker.objects_key, 0, -1)


def get_used_storage_by(worker_identity: str):
    _key = f"{worker_identity}:storage"
    used = _r.get(_key)
    if not used:
        return 0
    return int(used)


def get_object_by(filename: str) -> StoredObject:
    file_obj_data = _r.get(f"file:{filename}")
    if file_obj_data:
        return StoredObject.from_db(filename, file_obj_data)


def remove_worker_from_object(filename: str, worker: Worker):
    stored_object = get_object_by(filename)
    try:
        stored_object.workers.remove(worker)
    except ValueError:
        ...
    add_object(stored_object.filename, stored_object.workers)


def add_object(filename, workers: list[Worker]):
    stored_info = "::".join([w.key for w in workers])
    _r.set(f"file:{filename}", stored_info)
