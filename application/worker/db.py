import redis
from os import environ
import logging

REDIS_HOST = environ.get("REDIS_HOST", "127.0.0.1")

_r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)


def add_object_to_worker(whost, wport, filename: str, file_size: int):
    objects_in_worker = get_all_objects_by(whost, wport)
    logging.info(f"WORKER 1 {objects_in_worker}")
    already_present_object = None
    for obj in objects_in_worker:
        if obj.split(":")[0] == filename:
            already_present_object = obj
            break
    if already_present_object:
        old_size = already_present_object.split(":")[1]
        remove_object_by(whost, wport, filename, old_size)

    _r.rpush(f"{whost}:{wport}:objects", f"{filename}:{file_size}")
    _r.incr(f"{whost}:{wport}:storage", amount=file_size)


def remove_object_by(whost, wport, filename, file_size):
    _r.lrem(f"{whost}:{wport}:objects", 1, f"{filename}:{file_size}")
    _r.decr(f"{whost}:{wport}:storage", file_size)


def get_all_objects_by(whost, wport):
    return _r.lrange(f"{whost}:{wport}:objects", 0, -1)


def add_object(filename, whost, wport):
    current_workers = _r.get(f"file:{filename}")
    logging.info(f"WORKER 2 {current_workers}")
    if not current_workers or current_workers.split("::")[0] == '':
        _r.set(f"file:{filename}", f"{whost}:{wport}")
        return
    workers = current_workers.split("::")
    if f"{whost}:{wport}" not in workers:
        workers.append(f"{whost}:{wport}")
    stored_info = "::".join(workers)
    _r.set(f"file:{filename}", stored_info)
