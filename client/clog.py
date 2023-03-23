import os as os


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
