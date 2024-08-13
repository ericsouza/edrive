import server
import processor
import monitor

if __name__ == "__main__":
    server.start()
    monitor.start()

    # monitor need to be the last one started always
    processor.start()
