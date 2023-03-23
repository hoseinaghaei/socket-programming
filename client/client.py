import socket
import sys
import os.path as path
import asyncio
import _thread
from operator import methodcaller
import threading as thread
import random
from datetime import datetime as dt
from clog import Address

files = {}
files_lock = thread.Lock()
print_lock = thread.Lock()

tracker = Address()
me = Address()
LISTEN_QUEUE_SIZE = 5
BUFFER_SIZE = 1024
HEARTBEAT_INTERVAL = 10


def get_argv():
    if len(sys.argv) != 5:
        print('Not enough input!')
        exit(-1)
    else:
        tracker_addr = sys.argv[3].split(':')
        listen_addr = sys.argv[4].split(':')
        if len(tracker_addr) != 2 or len(tracker_addr[0].split('.')) != 4:
            print("Wrong tracker ip or port")
            exit(-1)
        if len(listen_addr) != 2 or len(listen_addr[0].split('.')) != 4:
            print("Wrong listen ip or port")
            exit(-1)

        return sys.argv[1], sys.argv[2], tracker_addr[0], int(tracker_addr[1]), listen_addr[0], int(listen_addr[1])


def msg(message):
    global print_lock
    print_lock.acquire(True, 1)
    print(message, flush=True)
    print_lock.release()


def send_heartbeat():
    global tracker, me
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(me.addr())
    client.sendto(b"heartbeat", tracker.addr())
    message, addr = client.recvfrom(BUFFER_SIZE)
    msg(f"heartbeat : {message.decode()}")
    client.close()


def handle_heartbeat():
    thread.Timer(HEARTBEAT_INTERVAL, handle_heartbeat).start()
    send_heartbeat()


def handle_request_share(file_addr: str):
    global files, files_lock, tracker, me
    if not path.isfile(file_addr):
        msg("file does not exist!")
        exit(-1)

    file_name = file_addr.split('/')[-1]
    files_lock.acquire(True, 1)
    files[file_name] = {
        'address': file_addr,
        'size': path.getsize(file_addr)
    }
    files_lock.release()

    message = f"share {file_name}"

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(me.addr())
    client.sendto(message.encode(), tracker.addr())


def download(peer_addr, file_name):
    global files, files_lock, me
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.bind(me.addr())
        client.connect(peer_addr)
        client.send(f"get {file_name}".encode())
        file_size = client.recv(BUFFER_SIZE).decode()

        while not file_size.isdigit():
            file_size = client.recv(BUFFER_SIZE).decode()

        msg(f"size : {file_size}")
        if file_size == 0:
            msg("ho")
            return False

        # me.create_dir_if_does_not_exist()
        file_addr = f"{me.dir()}/{file_name}"
        msg(file_addr)
        with open(file_addr, "wb+") as f:
            while True:
                bytes_read = client.recv(BUFFER_SIZE)
                if not bytes_read:
                    break
                f.write(bytes_read)

    files_lock.acquire(True, 1)
    files[file_name] = {
        'address': file_addr,
        'size': file_size
    }
    msg(files)
    files_lock.release()
    return True


def handle_request_get(file_name: str):
    global tracker, me
    message = f"get {file_name}"

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(me.addr())
    client.sendto(message.encode(), tracker.addr())

    message, addr = client.recvfrom(BUFFER_SIZE)
    while addr != tracker.addr():
        message, addr = client.recvfrom(BUFFER_SIZE)

    message = eval(message.decode())
    if len(message) < 1:
        msg('There is no seeder for this file')
        exit(-1)

    peer_to_download = message[random.randint(0, len(message) - 1)]
    msg(peer_to_download)

    if download(tuple(peer_to_download), file_name):
        message = f"done download {file_name} from {peer_to_download[0]}:{peer_to_download[1]}"
        me.create_dir_if_does_not_exist()
    else:
        message = f"failed download {file_name} from {peer_to_download[0]}:{peer_to_download[1]}"

    client.sendto(message.encode(), tracker.addr())
    client.close()


def handle_download_request(connection, addr):
    global files
    message = connection.recv(BUFFER_SIZE).decode().split()
    if len(message) != 2 or message[0] != 'get' or message[1] not in files.keys():
        size = 0
    else:
        size = files[message[1]]['size']

    connection.send(str(size).encode())
    connection.send("".encode())

    if size == 0:
        connection.close()
    else:
        with open(files[message[1]]['address'], "rb") as f:
            while True:
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    break

                connection.send(bytes_read)
            connection.close()


command_handler = {
    'get': {
        'func': 'handle_request_get'
    },
    'share': {
        'func': 'handle_request_share'
    },
    'user logs': {
        'func': 'print_user_logs'
    }
}


def start_client(command: str, file_name: str):
    global command_handler, me

    if command in command_handler.keys():
        func = globals()[command_handler[command]['func']]
        func(file_name)

        thread.Thread(target=handle_heartbeat).start()

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.bind(me.addr())
        client.listen(LISTEN_QUEUE_SIZE)
        while True:
            connection, addr = client.accept()
            thread.Thread(target=handle_download_request, args=[connection, addr]).start()


if __name__ == '__main__':
    # global tracker, me
    command, file_name, tracker_ip, tracker_port, listen_ip, listen_port = get_argv()
    me.set_ip(listen_ip).set_port(listen_port)
    tracker.set_ip(tracker_ip).set_port(tracker_port)
    me.create_dir_if_does_not_exist()
    start_client(command, file_name)
