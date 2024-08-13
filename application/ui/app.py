from flask import Flask, render_template
import db
from db import Worker, StoredObject
from datetime import datetime
import rq_dashboard
from os import environ

app = Flask(__name__)

REDIS_HOST = environ.get("REDIS_HOST", "127.0.0.1")

app.config.from_object(rq_dashboard.default_settings)
app.config["RQ_DASHBOARD_REDIS_URL"] = f"redis://{REDIS_HOST}:6379"
rq_dashboard.web.setup_rq_connection(app)
app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")

class User:
    def __init__(self, name, age, address, phone, email) -> None:
        self.name = name
        self.age = age
        self.address = address
        self.phone = phone
        self.email = email


@app.get("/")
def index():
    workers = db.get_all_workers()
    objects_in_workers = []
    workers_on_view = []
    objects_on_view = []
    for worker in workers:
        keepalive = db.get_keepalive(worker)
        objects = db.get_all_objects_by(worker)
        objects_in_workers.extend([obj for obj in objects])
        workers_on_view.append(worker_to_view(worker, keepalive, objects))

    unique_objects = set(objects_in_workers)
    for obj in unique_objects:
        stored_object = db.get_object_by(obj.split(":")[0])
        objects_on_view.append(object_to_view(stored_object, obj.split(":")[1]))

    return render_template(
        "index.html", workers=workers_on_view, objects=objects_on_view
    )


def worker_to_view(worker: Worker, keepalive: int, objects: list) -> dict:
    last_keep_alive = ""
    if keepalive:
        last_keep_alive = datetime.fromtimestamp(float(keepalive)).strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    return {
        "host": worker.host,
        "port": int(worker.port),
        "last_keepalive": last_keep_alive,
        "used_storage": worker.used_storage,
        "objects_quantity": len(objects),
    }


def object_to_view(object: StoredObject, file_size) -> dict:
    primary_worker = ""
    secondary_worker = ""

    try:
        primary_worker = object.workers[0].key
        secondary_worker = object.workers[1].key
    except IndexError:
        ...

    return {
        "filename": object.filename,
        "file_size": int(file_size),
        "primary_worker": primary_worker,
        "secondary_worker": secondary_worker,
    }


if __name__ == "__main__":
    app.run(debug=True)
