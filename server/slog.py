from datetime import datetime as dt
import threading as thread

file_lock = thread.Lock()


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

    def set_uploader_peer(self, peer: str):
        self.__server = peer
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
