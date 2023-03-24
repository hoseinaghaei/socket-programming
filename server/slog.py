from core import *

__get_file_logs = {}
__get_file_lock = thread.Lock()
__share_file_logs = {}
__share_file_lock = thread.Lock()
__file_logs = {}
__file_logs_lock = thread.Lock()
__seeder_logs = {}
__seeder_logs_lock = thread.Lock()


def create_get_file_log(ip: str, port: int, file_name: str, file_seeders: list) -> None:
    global __get_file_logs, __get_file_lock
    __get_file_lock.acquire(True, 1)
    client = Seeder.key(ip, port)
    log = GetFileLog(client=client, seeders=file_seeders, file_name=file_name)
    __get_file_logs[GetFileLog.key(client=client, file_name=file_name)] = log
    __get_file_lock.release()


def update_get_file_log(ip: str, port: int, file_name: str, uploader_seeder: str, success=True) -> GetFileLog:
    global __get_file_logs, __get_file_lock
    __get_file_lock.acquire(True, 1)
    client = Seeder.key(ip=ip, port=port)
    file_key = GetFileLog.key(client=client, file_name=file_name)
    __get_file_logs[file_key] \
        .set_success(success=success) \
        .set_uploader_peer(seeder=uploader_seeder)
    __get_file_lock.release()
    return __get_file_logs[file_key]


def create_share_file_log(ip: str, port: int, file_name: str) -> ShareFileLog:
    global __share_file_logs, __share_file_logs
    __share_file_lock.acquire(True, 1)
    client = Seeder.key(ip, port)
    log = ShareFileLog(peer=client, file_name=file_name)
    __share_file_logs[ShareFileLog.key(client, file_name)] = log
    __share_file_lock.release()
    return log


def add_share_log_to_file_log(file_name: str, share_file_log: ShareFileLog):
    global __file_logs, __file_logs_lock
    __file_logs_lock.acquire(True, 1)
    if file_name in __file_logs.keys():
        __file_logs[file_name].add_share_file_log(log=share_file_log)
    else:
        file_log = FileLog(file_name=file_name).add_share_file_log(log=share_file_log)
        __file_logs[file_name] = file_log
    __file_logs_lock.release()


def add_get_log_to_file_log(file_name: str, get_file_log: GetFileLog) -> None:
    global __file_logs, __file_logs_lock
    __file_logs_lock.acquire(True, 1)

    if file_name in __file_logs:
        __file_logs[file_name].add_get_file_log(log=get_file_log)
    else:
        file_log = FileLog(file_name).add_get_file_log(log=get_file_log)
        __file_logs[file_name] = file_log
    __file_logs_lock.release()


def add_share_log_to_user_log(seeder_key: str, share_file_log: ShareFileLog):
    global __seeder_logs, __seeder_logs_lock

    __seeder_logs_lock.acquire(True, 1)
    if seeder_key in __seeder_logs.keys():
        __seeder_logs[seeder_key].add_share_file_log(log=share_file_log)
    else:
        seeder_log = SeederLog(seeder_key=seeder_key).add_share_file_log(log=share_file_log)
        __seeder_logs[seeder_key] = seeder_log
    __seeder_logs_lock.release()


def add_get_log_to_user_log(seeder_key: str, get_file_log: GetFileLog) -> None:
    global __seeder_logs, __seeder_logs_lock

    __seeder_logs_lock.acquire(True, 1)
    if seeder_key in __seeder_logs.keys():
        __seeder_logs[seeder_key].add_get_file_log(log=get_file_log)
    else:
        seeder_log = SeederLog(seeder_key=seeder_key).add_get_file_log(log=get_file_log)
        __seeder_logs[seeder_key] = seeder_log
    __seeder_logs_lock.release()


def update_seeder_last_heartbeat_log(seeder_key: str) -> None:
    global __seeder_logs, __seeder_logs_lock

    __seeder_logs_lock.acquire(blocking=True, timeout=1)
    if seeder_key in __seeder_logs.keys():
        __seeder_logs[seeder_key].update_heartbeat()
    else:
        seeder_log = SeederLog(seeder_key=seeder_key)
        __seeder_logs[seeder_key] = seeder_log

    __seeder_logs_lock.release()


def get_file_all_logs(file_name: str):
    global __file_logs
    if file_name not in __file_logs.keys():
        return None
    else:
        return __file_logs[file_name].get_log_formatted()


def get_seeder_all_logs(seeder_key: str):
    global __file_logs
    if seeder_key not in __seeder_logs.keys():
        return None
    else:
        return __seeder_logs[seeder_key].get_log_formatted()


def get_request_logs():
    get_file = []
    for i in __get_file_logs:
        get_file.append(i.get_log_formatted())

    share_file = []
    for i in __share_file_logs:
        share_file.append(i.get_log_formatted())

    return {
        'get_log': get_file,
        'share_log': share_file
    }
