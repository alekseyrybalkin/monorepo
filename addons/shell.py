import getpass
import os
import subprocess
import sys


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


def user():
    return getpass.getuser()


def home(user=None):
    if user is None:
        user = getpass.getuser()
    home_with_expansion = '~{}'.format(user)
    home = os.path.expanduser(home_with_expansion)
    if home == home_with_expansion:
        raise RuntimeError('no such user {}'.format(user))
    return home


def colorize(text, color=7):
    if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
        seq = "\x1b[1;{}m".format(30 + color) + text + "\x1b[0m"
        return seq
    return text
