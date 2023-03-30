from clog import *
import pprint

print_lock = thread.Lock()


def msg(message) -> None:
    global print_lock
    print_lock.acquire(blocking=True, timeout=1)
    pprint.pprint(message, sort_dicts=False, underscore_numbers=True)
    print_lock.release()


def __print_request_log(argv: list):
    logs = get_request_logs()
    msg(logs)


def __shout_down(argv: list):
    msg("Client shutting down the input...\nSIGINT to kill the main thread!")
    exit(-1)


cli_handler = {
    'request logs': {
        'func': '__print_request_log'
    },
    'quit': {
        'func': '__shout_down'
    }
}


def handle_input_cli():
    global cli_handler
    while True:
        command = input()
        split_command = command.split()
        if len(command) == 0:
            continue
        if command in cli_handler:
            func = globals()[cli_handler[command]['func']]
            func(split_command)
        elif split_command[0] in cli_handler:
            func = globals()[cli_handler[split_command[0]]['func']]
            func(split_command)
        else:
            msg('invalid command!')
