import os.path as path
import random
import socket
import sys
import threading as thread

from entity import Address
from clog import create_share_file_log, create_get_file_log
from client_cli import handle_input_cli, msg

__files = {}
__files_lock = thread.Lock()
print_lock = thread.Lock()

tracker = Address()
me = Address()
LISTEN_QUEUE_SIZE = 5
BUFFER_SIZE = 1024
HEARTBEAT_INTERVAL = 10
WAITING_COUNT_FOR_RELATED_RESPONSE = 5


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


def quit(message: str, client: socket):
    client.close()
    msg(message=message)
    exit(-1)


def send_heartbeat():
    global tracker, me
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(me.addr())
    client.sendto(b"heartbeat", tracker.addr())
    client.close()


def handle_heartbeat():
    global HEARTBEAT_INTERVAL
    thread.Timer(HEARTBEAT_INTERVAL, handle_heartbeat).start()
    send_heartbeat()


def __add_new_file(file_name: str, file_address: str, size: int):
    global __files, __files_lock
    __files_lock.acquire(True, 1)
    __files[file_name] = {
        'address': file_address,
        'size': size
    }
    __files_lock.release()


def handle_request_share(file_address: str) -> None:
    global __files, __files_lock, tracker, me
    if not path.isfile(file_address):
        msg("file does not exist!")
        exit(-1)

    file_name = file_address.split('/')[-1]

    message = f"share {file_name}"

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(me.addr())
    client.sendto(message.encode(), tracker.addr())
    for i in range(WAITING_COUNT_FOR_RELATED_RESPONSE):
        response, addr = client.recvfrom(BUFFER_SIZE)
        if response.decode() == f"{message} done":
            __add_new_file(file_name=file_name, file_address=file_address, size=path.getsize(file_addr))
            client.close()
            return

    quit("share file failed", client)


def download(peer_addr: tuple, file_name: str):
    global __files, __files_lock, me
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.bind(me.addr())
        try:
            client.connect(peer_addr)
            client.send(f"get {file_name}".encode())
            for i in range(WAITING_COUNT_FOR_RELATED_RESPONSE):
                response = client.recv(BUFFER_SIZE).decode()
                if response.startswith('\nsize:'):
                    file_size = response.split('\n')[1].split(':')[-1]
                    if not file_size.isdigit() or file_size == 0:
                        return False

                    me.create_dir_if_does_not_exist()
                    file_address = f"{me.dir()}/{file_name}"
                    with open(file_address, "wb+") as f:
                        while True:
                            bytes_read = client.recv(BUFFER_SIZE)
                            if not bytes_read:
                                break
                            f.write(bytes_read)
                    __add_new_file(file_name=file_name, file_address=file_address, size=int(file_size))
                    return True
            return False
        except:
            client.close()
            return False


def handle_request_get(file_name: str):
    global tracker, me
    message = f"get {file_name}"

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        # socket.setdefaulttimeout(1) todo: handle wait indefinitely
        client.bind(me.addr())
        client.sendto(message.encode(), tracker.addr())

        for i in range(WAITING_COUNT_FOR_RELATED_RESPONSE):
            message, addr = client.recvfrom(BUFFER_SIZE)
            message = message.decode()
            if message.startswith("seeders"):
                message = eval(message.split(':')[-1])
                if type(message) != list or len(message) < 1:
                    quit("There is no seeder for this file", client)

                peer_to_download = message[random.randint(0, len(message) - 1)]

                download_success = download(tuple(peer_to_download), file_name)
                if download_success:
                    response = f"done download {file_name} from {peer_to_download[0]}:{peer_to_download[1]}"
                else:
                    response = f"failed download {file_name} from {peer_to_download[0]}:{peer_to_download[1]}"
                msg(response)
                client.sendto(response.encode(), tracker.addr())
                if not download_success:
                    quit('download file failed', client)
                create_get_file_log(file_name=file_name, peer=peer_to_download, seeders=message)
                return

    quit("get file failed", client)


def handle_download_request(connection, addr):
    global __files
    message = connection.recv(BUFFER_SIZE).decode().split()
    if len(message) != 2 or message[0] != 'get' or message[1] not in __files.keys():
        size = 0
    else:
        size = __files[message[1]]['size']
        msg(f"Peer connected from {addr} to get {message[1]}")

    try:
        connection.send(f"\nsize:{size}\n".encode())
        connection.sendall("".encode())

        if size == 0:
            connection.close()
        else:
            with open(__files[message[1]]['address'], "rb") as f:
                while True:
                    bytes_read = f.read(BUFFER_SIZE)
                    if not bytes_read:
                        break

                    connection.send(bytes_read)
                connection.close()
            create_share_file_log(file_name=message[1], peer=str(addr), success=True)
    except:
        connection.close()
        create_share_file_log(file_name=message[1], peer=str(addr), success=False)


command_handler = {
    'get': {
        'func': 'handle_request_get'
    },
    'share': {
        'func': 'handle_request_share'
    }
}


def start_client(command: str, file_name: str):
    global command_handler, me

    if command in command_handler.keys():
        func = globals()[command_handler[command]['func']]
        func(file_name)

        thread.Thread(target=handle_heartbeat).start()
        thread.Thread(target=handle_input_cli).start()

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.bind(me.addr())
        client.listen(LISTEN_QUEUE_SIZE)
        while True:
            connection, addr = client.accept()
            thread.Thread(target=handle_download_request, args=[connection, addr]).start()


if __name__ == '__main__':
    command, file_addr, tracker_ip, tracker_port, listen_ip, listen_port = get_argv()
    me.set_ip(listen_ip).set_port(listen_port)
    tracker.set_ip(tracker_ip).set_port(tracker_port)
    start_client(command, file_addr)
