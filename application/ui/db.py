import redis

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


def get_all_workers() -> list[Worker]:
    all_workers = _r.lrange(WORKERS_LIST_KEY, 0, -1)
    workers = []
    for worker in all_workers:
        used_storage = get_used_storage_by(worker_identity=worker)
        workers.append(Worker.from_db(key=worker, used_storage=used_storage))
    return workers

def get_keepalive(worker: Worker) -> bool:
    return _r.get(worker.keepalive_key)

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

