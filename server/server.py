import socket
import sys

from server_cli import msg, handle_input_cli
from slog import *
from core import *

BUFFER_SIZE = 1024


def handle_client_get_request(argv: list, peer_ip: str, peer_port: int) -> str:
    msg("Pear connected from" + f" {peer_ip}:{peer_port} for get")

    file_name = argv[1]
    file_seeders = find_seeders_for_file(file_name)
    create_get_file_log(ip=peer_ip, port=peer_port, file_name=file_name, file_seeders=file_seeders)

    return f"seeders :{file_seeders}"


def handle_client_share_request(argv: list, seeder_ip: str, seeder_port: int) -> str:
    msg("Pear connected from" + f" {seeder_ip}:{seeder_port} for share")

    file_name = argv[1]
    add_new_file_and_seeder(ip=seeder_ip, port=seeder_port, file_name=file_name)
    log = create_share_file_log(ip=seeder_ip, port=seeder_port, file_name=file_name)
    add_share_log_to_file_log(file_name=file_name, share_file_log=log)
    add_share_log_to_user_log(seeder_key=Seeder.key(ip=seeder_ip, port=seeder_port), share_file_log=log)
    return f"share {file_name} done"


def handle_heartbeat(argv: list, seeder_ip: str, seeder_port: int) -> str:
    heartbeat = update_heartbeat(ip=seeder_ip, port=seeder_port)
    if heartbeat is None:
        return "you are not a seeder!"
    update_seeder_last_heartbeat_log(Seeder.key(ip=seeder_ip, port=seeder_port))
    return heartbeat


def handle_download_completed(argv: list, new_seeder_ip: str, new_seeder_port: int) -> None:
    file_name = argv[2]
    add_new_file_and_seeder(ip=new_seeder_ip, port=new_seeder_port, file_name=file_name)
    log = update_get_file_log(uploader_seeder=argv[4], file_name=file_name, ip=new_seeder_ip, port=new_seeder_port)
    add_get_log_to_file_log(file_name=file_name, get_file_log=log)
    add_get_log_to_user_log(seeder_key=Seeder.key(ip=new_seeder_ip, port=new_seeder_port), get_file_log=log)
    add_get_log_to_user_log(seeder_key=argv[4], get_file_log=log)


def handle_download_failed(argv: list, peer_ip: str, peer_port: int):
    file_name = argv[2]
    log = update_get_file_log(uploader_seeder=argv[4], file_name=file_name, ip=peer_ip, port=peer_port, success=False)
    add_get_log_to_file_log(file_name=file_name, get_file_log=log)


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
    global message_handler
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


def get_addr():
    if len(sys.argv) <= 1:
        print("no ip or port")
        exit(-1)
    addr = sys.argv[1].split(':')
    if len(addr) != 2 or len(addr[0].split('.')) != 4:
        print("wrong ip or port")
        exit(-1)
    return addr


def listen(ip: str, port: int):
    msg("Server is running on " + f"{ip}:{port}")
    thread.Thread(target=handle_input_cli).start()
    server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    server.bind((ip, port))

    while True:
        message, addr = server.recvfrom(BUFFER_SIZE)
        thread.Thread(target=handle_client, args=[message.decode(), addr, server]).start()


if __name__ == '__main__':
    tracker_ip, tracker_port = get_addr()
    listen(ip=tracker_ip, port=int(tracker_port))
