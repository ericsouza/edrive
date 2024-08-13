import db
from time import sleep
import logging
import threading
from datetime import datetime, timedelta
from processor import enqueue_worker_died


def monitor_workers():
    while True:
        sleep(10)

        workers = db.get_all_workers()
        for worker in workers:
            keepalive = db.get_keepalive(worker)
            is_alive = (
                keepalive is not None
                and datetime.now()
                <= datetime.fromtimestamp(float(keepalive)) + timedelta(seconds=30)
            )
            if not is_alive:
                msg = f"{worker} will be removed from available workers because no keepalive was seen."
                if keepalive:
                    msg = f"{msg} Last keepalive was at {datetime.fromtimestamp(float(keepalive))}"
                # servidor não mandou keepalive há muito tempo
                # precisamos remove-lo da lista de disponíveis
                logging.warning(msg)
                enqueue_worker_died(worker)


def start():
    monitor_thread = threading.Thread(target=monitor_workers, daemon=True)
    monitor_thread.start()
