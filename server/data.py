from datetime import datetime as dt

HEARTBEAT_TIMEOUT = 30


class File:
    def __init__(self, name: str, seeder: str):
        self.__name = name
        self.__seeders = {seeder: seeder}

    def name(self):
        return self.__name

    def add_seeder(self, seeder: str):
        self.__seeders[seeder] = seeder

    def seeders(self):
        return self.__seeders


class Seeder:
    def __init__(self, ip: str, port: int, file_name):
        self.__ip = ip
        self.__port = port
        self.__files = {}
        self.__heartbeat = dt.now()
        if file_name is not None:
            self.__files[file_name] = file_name

    def add_file(self, file):
        self.__files[file] = file
        return self

    def get_file(self, name):
        if name in self.__files:
            return self.__files[name]
        return None

    def files(self):
        return self.__files

    def ip(self):
        return self.__ip

    def port(self):
        return self.__port

    def update_heartbeat(self):
        self.__heartbeat = dt.now()
        return self

    def formatted_heartbeat(self):
        return self.__heartbeat.strftime("%Y-%m-%d %H:%M:%S")

    def heartbeat(self):
        return self.__heartbeat

    def addr(self):
        return f"{self.__ip}:{self.__port}"

    def is_alive(self):
        return (dt.now() - self.heartbeat()).seconds < HEARTBEAT_TIMEOUT

    @staticmethod
    def key(ip, port):
        return f"{ip}:{port}"
