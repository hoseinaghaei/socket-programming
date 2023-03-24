from datetime import datetime as dt
import threading as thread
from core import *

file_lock = thread.Lock()

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


def update_get_file_log(ip: str, port: int, file_name: str, uploader_seeder: str, success: bool) -> GetFileLog:
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


def add_share_log_to_file_log(file_name: str, log: ShareFileLog):
    global __file_logs, __file_logs_lock
    __file_logs_lock.acquire(True, 1)
    if file_name in __file_logs.keys():
        __file_logs[file_name].add_share_file_log(log=log)
    else:
        file_log = FileLog(file_name=file_name).add_share_file_log(log=log)
        __file_logs[file_name] = file_log
    __file_logs_lock.release()


def add_get_log_to_file_log(file_name: str, log: GetFileLog) -> None:
    global __file_logs, __file_logs_lock
    __file_logs_lock.acquire(True, 1)
    if file_name in __file_logs:
        __file_logs[file_name].add_get_file_log(log=log)
    else:
        file_log = FileLog(file_name).add_get_file_log(log=log)
        __file_logs[file_name] = file_log
    __file_logs_lock.release()


def get_file_all_logs(file_name: str):
    global __file_logs
    if file_name not in __file_logs.keys():
        return None
    else:
        return __file_logs[file_name].get_log_formatted()
