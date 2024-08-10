import server
import processor
import monitor
import logging

logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if __name__ == "__main__":
    server.start()
    monitor.start()

    # monitor need to be the last one started always
    processor.start()
