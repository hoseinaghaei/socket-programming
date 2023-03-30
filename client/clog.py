from entity import *
import threading as thread

__get_file_logs = []
__get_file_lock = thread.Lock()
__send_file_logs = []
__send_file_lock = thread.Lock()


def create_get_file_log(file_name: str, peer: str, seeders: list) -> None:
    global __get_file_logs, __get_file_lock
    __get_file_lock.acquire(blocking=True, timeout=1)
    log = GetFileLog(file_name=file_name, peer=peer, seeders=seeders)
    __get_file_logs.append(log)
    __get_file_lock.release()


def create_share_file_log(file_name: str, peer: str, success: bool) -> None:
    global __send_file_logs, __send_file_lock
    __send_file_lock.acquire(blocking=True, timeout=1)
    log = SendFileLog(file_name=file_name, peer=peer, success=success)
    __send_file_logs.append(log)
    __send_file_lock.release()


def get_request_logs():
    global __get_file_logs, __send_file_logs
    get_file = []
    for i in __get_file_logs:
        get_file.append(i.get_log_formatted())

    send_file = []
    for i in __send_file_logs:
        send_file.append(i.get_log_formatted())

    return {
        'get_log': get_file,
        'send_log': send_file
    }
