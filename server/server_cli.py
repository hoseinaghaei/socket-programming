import pprint
from slog import *

print_lock = thread.Lock()


def msg(message) -> None:
    global print_lock
    print_lock.acquire(blocking=True, timeout=1)
    pprint.pprint(message, sort_dicts=False, underscore_numbers=True)
    print_lock.release()


def __print_request_log(argv: list):
    msg(get_request_logs())


def __print_user_logs(argv: list):
    seeder_key = argv[1]
    logs = get_seeder_all_logs(seeder_key=seeder_key)
    if logs is None:
        msg(f'{seeder_key} is not a seeder!')
    else:
        msg(logs)


def __print_file_logs(argv: list):
    file_name = argv[1]
    logs = get_file_all_logs(file_name)
    if file_name is None:
        msg(f"there is no log for file : {file_name}")
    else:
        msg(logs)


def __shout_down(argv: list):
    msg("Server shutting down the input...\nSIGINT to kill the main thread!")
    exit(-1)


command_handler = {
    'request logs': {
        'func': '__print_request_log'
    },
    'file_logs': {
        'func': '__print_file_logs'
    },
    'quit': {
        'func': '__shout_down'
    },
    'user_logs': {
        'func': '__print_user_logs'
    }
}


def handle_input_cli():
    global command_handler
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
