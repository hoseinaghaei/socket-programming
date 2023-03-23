import socket
import sys
import pprint
from slog import *

from core import Seeder, File

seeders = {}
seeders_lock = thread.Lock()
files = {}
files_lock = thread.Lock()

print_lock = thread.Lock()


def msg(message) -> None:
    global print_lock
    print_lock.acquire(blocking=True, timeout=1)
    pprint.pprint(message, sort_dicts=False, underscore_numbers=True)
    print_lock.release()


def add_new_seeder(ip: str, port: int) -> Seeder:
    global seeders
    new_peer = Seeder(ip=ip, port=port, file_name=None)
    seeders[new_peer.addr()] = new_peer
    return new_peer


def remove_seeder(ip: str, port: int) -> None:
    global seeders
    seeders_lock.acquire(blocking=True, timeout=1)

    peer_to_remove = seeders.pop(Seeder.key(ip=ip, port=port))
    remove_seeder_files(peer_to_remove)

    seeders_lock.release()


def remove_seeder_files(seeder: Seeder) -> None:
    global files
    for file_name in seeder.files():
        file_seeders = files[file_name].seeders()
        if len(file_seeders) == 1:
            files.pop(file_name)
        else:
            file_seeders.pop(seeder.addr())


def find_seeders_for_file(file_name: str) -> list:
    global files, files_lock, seeders
    files_lock.acquire(blocking=True, timeout=1)

    file_seeders = []
    dead_seeders = []
    if file_name in files.keys():
        for seeder_key in files[file_name].seeders():
            seeder = seeders[seeder_key]
            if seeder.is_alive():
                file_seeders.append((seeder.ip(), seeder.port()))
            else:
                dead_seeders.append((seeder.ip(), seeder.port()))

    for ip, port in dead_seeders:
        remove_seeder(ip=ip, port=port)

    files_lock.release()
    return file_seeders


def handle_client_get_request(command, ip: str, port: int) -> list:
    msg("Pear connected from" + f" {ip}:{port} for get")

    file_name = command[1]
    file_seeders = find_seeders_for_file(file_name)
    create_get_file_log(ip=ip, port=port, file_name=file_name, file_seeders=file_seeders)

    return file_seeders


def add_new_file_and_seeder(ip: str, port: int, file_name: str):
    global files, seeders, seeders_lock, files_lock
    seeder_key = Seeder.key(ip, port)

    files_lock.acquire(blocking=True, timeout=1)
    seeders_lock.acquire(blocking=True, timeout=1)

    if seeder_key in seeders.keys():
        seeder = seeders[seeder_key]
        if file_name in files.keys():
            files[file_name].add_seeder(seeder_key)
            seeder.add_file(file_name)
        else:
            new_file = File(name=file_name, seeder=seeder_key)
            seeder.add_file(file_name)
            files[file_name] = new_file
    else:
        new_seeder = add_new_seeder(ip, port)
        new_seeder.add_file(file_name)
        if file_name in files.keys():
            files[file_name].add_seeder(seeder_key)
        else:
            new_file = File(name=file_name, seeder=seeder_key)
            files[file_name] = new_file

    files_lock.release()
    seeders_lock.release()


def handle_client_share_request(command, ip: str, port: int) -> None:
    global seeders
    msg("Pear connected from" + f" {ip}:{port} for share")

    file_name = command[1]
    add_new_file_and_seeder(ip=ip, port=port, file_name=file_name)
    log = create_share_file_log(ip=ip, port=port, file_name=file_name)
    add_share_log_to_file_log(file_name=file_name, log=log)


def handle_heartbeat(argv: list, ip: str, port: int) -> str:
    global seeders, seeders_lock
    seeder_key = Seeder.key(ip, port)
    if seeder_key not in seeders.keys():
        return "you are not a seeder!"

    seeders_lock.acquire(blocking=True, timeout=1)
    seeders[seeder_key].update_heartbeat()
    seeders_lock.release()
    return seeders[seeder_key].formatted_heartbeat()


def handle_download_completed(argv: list, ip: str, port: int) -> None:
    file_name = argv[2]
    add_new_file_and_seeder(ip=ip, port=port, file_name=file_name)
    log = update_get_file_log(uploader_seeder=argv[4], file_name=file_name, ip=ip, port=port, success=True)
    add_get_log_to_file_log(file_name=file_name, log=log)


def handle_download_failed(argv: list, ip: str, port: int):
    pass


message_handler = {
    'get': {
        'func': 'handle_client_get_request',
        'argc': 2
    },
    'share': {
        'func': 'handle_client_share_request',
        'argc': 2
    },
    'heartbeat': {
        'func': 'handle_heartbeat',
        'argc': 1
    },
    'done': {
        'func': 'handle_download_completed',
        'argc': 5
    },
    'failed': {
        'func': 'handle_download_failed',
        'argc': 5
    }
}


def handle_client(message: str, addr: tuple, server: socket) -> None:
    global message_handler, seeders
    command = message.split()
    if len(message) != 0 and command[0] in message_handler:
        if len(command) != message_handler[command[0]]['argc']:
            res = 'Not enough argument!'
        else:
            func = globals()[message_handler[command[0]]['func']]
            res = str(func(command, addr[0], addr[1]))
    else:
        res = 'Invalid command!'

    server.sendto(res.encode(), addr)


def print_request_log(command):
    msg("print_request_log triggerd!")

    print(command)


def print_user_logs(command):
    global seeders
    msg("print_user_logs triggerd!")
    msg(seeders[command[2]])


def print_file_logs(command):
    file_name = command[1]
    logs = get_file_all_logs(file_name)
    if file_name is None:
        msg(f"there is no log for file : {file_name}")
    else:
        msg(logs)


def shout_down(command):
    msg("Server shutting down the input...\nSIGINT to kill the main thread!")
    exit(-1)


def handle_input_cli():
    command_handler = {
        'request logs': {
            'func': 'print_request_log'
        },
        'file_logs': {
            'func': 'print_file_logs'
        },
        'quit': {
            'func': 'shout_down'
        },
        'user_logs': {
            'func': 'print_user_logs'
        }
    }
    while True:
        command = input()
        split_command = command.split()
        if len(command) == 0:
            continue
        if command in command_handler:
            func = globals()[command_handler[command]['func']]
            func(split_command)
        elif split_command[0] in command_handler:
            func = globals()[command_handler[split_command[0]]['func']]
            func(split_command)
        else:
            msg('invalid command!')


def get_addr():
    if len(sys.argv) <= 1:
        print("no ip or port")
        exit(-1)
    addr = sys.argv[1].split(':')
    if len(addr) != 2 or len(addr[0].split('.')) != 4:
        print("wrong ip or port")
        exit(-1)
    return addr


def start_to_listen(ip: str, port: int):
    msg("Server is running on " + f"{ip}:{port}")
    thread.Thread(target=handle_input_cli).start()
    server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    server.bind((ip, port))

    buffer_size = 1024
    while True:
        message, addr = server.recvfrom(buffer_size)
        thread.Thread(target=handle_client, args=[message.decode(), addr, server]).start()


if __name__ == '__main__':
    ip, port = get_addr()
    start_to_listen(ip, int(port))
