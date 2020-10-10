import getpass
import os
import subprocess


def run(command, shell=False, strip=True):
    if isinstance(command, str):
        command = command.split(' ')

    if strip:
        return subprocess.check_output(command, shell=shell).strip().decode()
    else:
        return subprocess.check_output(command, shell=shell).decode()


def copy_to_clipboard(value):
    subprocess.run(
        ['xclip', '-selection', 'clipboard'],
        input=value,
        encoding='UTF-8',
    )


def home(user=None):
    if user is None:
        user = getpass.getuser()
    return os.path.expanduser('~{}'.format(user))
