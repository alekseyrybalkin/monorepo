import getpass
import os
import subprocess


def run(command, shell=False, strip=True, input_bytes=None):
    if isinstance(command, str):
        command = command.split(' ')

    options = {
        'shell': shell,
    }
    if input_bytes:
        options['input'] = input_bytes

    result = subprocess.check_output(command, **options).decode()

    if strip:
        return result.strip()
    return result


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
