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
    def __init__(self, ip: str, port: int):
        self.__ip = ip
        self.__port = port
        self.__files = {}
        self.__heartbeat = dt.now()

    def add_file(self, file_name: str):
        self.__files[file_name] = file_name
        return self

    def get_file(self, file_name: str):
        if file_name in self.__files:
            return self.__files[file_name]
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
        self.__get_file_logs.append(log)
        return self

    def add_share_file_log(self, log: ShareFileLog):
        self.__share_file_logs.append(log)
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


class SeederLog:
    def __init__(self, seeder_key: str):
        self.__seeder_key = seeder_key
        self.__heartbeat = dt.now()
        self.__get_file_logs = []
        self.__share_file_logs = []

    def add_get_file_log(self, log: GetFileLog):
        self.__get_file_logs.append(log)
        return self

    def add_share_file_log(self, log: ShareFileLog):
        self.__share_file_logs.append(log)
        return self

    def update_heartbeat(self):
        self.__heartbeat = dt.now()

    def get_log_formatted(self):
        get_file = []
        for i in self.__get_file_logs:
            get_file.append(i.get_log_formatted())

        share_file = []
        for i in self.__share_file_logs:
            share_file.append(i.get_log_formatted())

        return {
            'seeder': self.__seeder_key,
            'last_heartbeat': self.__heartbeat.strftime("%Y-%m-%d %H:%M:%S"),
            'get_log': get_file,
            'share_log': share_file
        }
