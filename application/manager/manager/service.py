import db

def select_worker(exclude: list[db.Worker] = [], include: list[db.Worker] = []):
    # primeiro vemos se foi passada uma lista "forçada" para salvar os arquivos
    forced_workers = list(set(include) - set(exclude))
    if forced_workers:
        return forced_workers[0]

    # senao, é pq o arquivo é novo no sistema e elegemos outro
    workers = db.get_all_workers()
    available_workers = [w for w in workers if w not in exclude]
    sorted_available_workers = sorted(available_workers, key=lambda w: w.used_storage)
    return sorted_available_workers[0]
