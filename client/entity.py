import os as os
from datetime import datetime as dt


class Address:
    def __init__(self, ip='', port=0):
        self.__ip = ip
        self.__port = port

    def addr(self):
        return tuple([self.__ip, self.__port])

    def set_ip(self, ip: str):
        self.__ip = ip
        return self

    def set_port(self, port: int):
        self.__port = port
        return self

    def dir(self):
        return f"{self.__port}"

    def create_dir_if_does_not_exist(self):
        os.makedirs(name=f"{os.getcwd()}/{self.dir()}", exist_ok=True)


class SendFileLog:
    def __init__(self, file_name: str, peer: str, success: bool):
        self.__file_name = file_name
        self.__created_at = dt.now()
        self.__peer = peer
        self.__success = success

    def get_log_formatted(self):
        return {
            'peer': self.__peer,
            'file_name': self.__file_name,
            'success': self.__success,
            'created_at': self.__created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class GetFileLog:
    def __init__(self, file_name: str, peer: str, seeders: list):
        self.__file_name = file_name
        self.__created_at = dt.now()
        self.__peer = peer
        self.__seeders = seeders

    def get_log_formatted(self):
        return {
            'peer': self.__peer,
            'file_name': self.__file_name,
            'created_at': self.__created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'seeders': self.__seeders
        }
