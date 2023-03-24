from datetime import datetime as dt
import threading as thread

HEARTBEAT_TIMEOUT = 30

__seeders = {}
__seeders_lock = thread.Lock()
__files = {}
__files_lock = thread.Lock()


def create_seeder(ip: str, port: int) -> Seeder:
    global __seeders
    new_peer = Seeder(ip=ip, port=port)
    __seeders[new_peer.addr()] = new_peer
    return new_peer


def find_seeders_for_file(file_name: str) -> list:
    global __files, __files_lock, __seeders
    __files_lock.acquire(blocking=True, timeout=1)

    file_seeders = []
    dead_seeders = []
    if file_name in __files.keys():
        for seeder_key in __files[file_name].seeders():
            seeder = __seeders[seeder_key]
            if seeder.is_alive():
                file_seeders.append((seeder.ip(), seeder.port()))
            else:
                dead_seeders.append((seeder.ip(), seeder.port()))

    for ip, port in dead_seeders:
        __remove_seeder_with_related_files(ip=ip, port=port)

    __files_lock.release()
    return file_seeders


def add_new_file_and_seeder(ip: str, port: int, file_name: str):
    global __files, __seeders, __seeders_lock, __files_lock
    seeder_key = Seeder.key(ip, port)

    __files_lock.acquire(blocking=True, timeout=1)
    __seeders_lock.acquire(blocking=True, timeout=1)

    if seeder_key in __seeders.keys():
        seeder = __seeders[seeder_key]
        if file_name in __files.keys():
            __files[file_name].add_seeder(seeder_key)
            seeder.add_file(file_name)
        else:
            new_file = File(name=file_name, seeder=seeder_key)
            seeder.add_file(file_name)
            __files[file_name] = new_file
    else:
        new_seeder = create_seeder(ip, port)
        new_seeder.add_file(file_name)
        if file_name in __files.keys():
            __files[file_name].add_seeder(seeder_key)
        else:
            new_file = File(name=file_name, seeder=seeder_key)
            __files[file_name] = new_file

    __files_lock.release()
    __seeders_lock.release()


def update_heartbeat(ip: str, port: int):
    global __seeders, __seeders_lock

    seeder_key = Seeder.key(ip, port)
    if seeder_key not in __seeders.keys():
        return None

    __seeders_lock.acquire(blocking=True, timeout=1)
    __seeders[seeder_key].update_heartbeat()
    __seeders_lock.release()
    return __seeders[seeder_key].formatted_heartbeat()


def __remove_seeder_with_related_files(ip: str, port: int) -> None:
    global __seeders, __seeders_lock
    __seeders_lock.acquire(blocking=True, timeout=1)

    seeder_to_remove = __seeders.pop(Seeder.key(ip=ip, port=port))
    __remove_seeder_files(seeder_to_remove)

    __seeders_lock.release()


def __remove_seeder_files(seeder: Seeder) -> None:
    global __files
    for file_name in seeder.files():
        file_seeders = __files[file_name].seeders()
        if len(file_seeders) == 1:
            __files.pop(file_name)
        else:
            file_seeders.pop(seeder.addr())
