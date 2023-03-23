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


class GetFileLog:
    def __init__(self, client: str, seeders: list, file_name: str):
        self.__client = client
        self.__server = None
        self.__seeders = seeders
        self.__success = False
        self.__start_at = dt.now()
        self.__finished_at = None
        self.__file_name = file_name

    def set_success(self, success: bool):
        self.__success = success
        self.__finished_at = dt.now()
        return self

    def set_uploader_peer(self, seeder: str):
        self.__server = seeder
        return self

    @staticmethod
    def key(client: str, file_name: str):
        return f"{client}-{file_name}"

    def get_log_formatted(self):
        finish_at = self.__finished_at
        if finish_at is not None:
            finish_at = self.__finished_at.strftime("%Y-%m-%d %H:%M:%S")
        return {
            'peer': self.__client,
            'server': self.__server,
            'file_name': self.__file_name,
            'seeders': self.__seeders,
            'success': self.__success,
            'started_at': self.__start_at.strftime("%Y-%m-%d %H:%M:%S"),
            'finished_at': finish_at
        }


class ShareFileLog:
    def __init__(self, peer: str, file_name: str):
        self.__peer = peer
        self.__created_at = dt.now()
        self.__file_name = file_name

    def get_log_formatted(self):
        return {
            'peer': self.__peer,
            'file_name': self.__file_name,
            'created_at': self.__created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

    @staticmethod
    def key(client: str, file_name: str):
        return f"{client}-{file_name}"


class FileLog:
    def __init__(self, file_name: str):
        self.__file_name = file_name
        self.__get_file_logs = []
        self.__share_file_logs = []

    def add_get_file_log(self, log: GetFileLog):
        file_lock.acquire(True, 1)
        self.__get_file_logs.append(log)
        file_lock.release()
        return self

    def add_share_file_log(self, log: ShareFileLog):
        file_lock.acquire(True, 1)
        self.__share_file_logs.append(log)
        file_lock.release()
        return self

    def get_log_formatted(self):
        get_file = []
        for i in self.__get_file_logs:
            get_file.append(i.get_log_formatted())

        share_file = []
        for i in self.__share_file_logs:
            share_file.append(i.get_log_formatted())

        return {
            'file_name': self.__file_name,
            'get_log': get_file,
            'share_log': share_file
        }


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
