import getpass
import os
import subprocess
import sys


def run(command, shell=False, silent=False, user=None, group=None, tee=None):
    if not shell and isinstance(command, str):
        command = command.split(' ')

    options = {
        'stdout': subprocess.PIPE,
        'stderr': subprocess.STDOUT,
        'shell': shell,
        'user': user,
        'group': group,
    }

    if tee:
        tee_log = open(tee, 'tw')

    with subprocess.Popen(command, **options) as proc:
        while proc.poll() is None:
            while True:
                line = proc.stdout.readline().decode()
                if line:
                    if not silent:
                        sys.stdout.write(line)
                    if tee:
                        tee_log.write(line)
                else:
                    break
        while True:
            line = proc.stdout.readline().decode()
            if line:
                if not silent:
                    sys.stdout.write(line)
                if tee:
                    tee_log.write(line)
            else:
                break

    if tee:
        tee_log.close()

    if proc.poll() != 0:
        raise subprocess.CalledProcessError(proc.poll(), command)


def output(command, shell=False, strip=True, silent=True, user=None, group=None):
    if not shell and isinstance(command, str):
        command = command.split(' ')

    options = {
        'stdout': subprocess.PIPE,
        'stderr': subprocess.STDOUT,
        'shell': shell,
        'user': user,
        'group': group,
    }

    with subprocess.Popen(command, **options) as proc:
        output = ''
        while proc.poll() is None:
            while True:
                line = proc.stdout.readline().decode()
                if line:
                    if not silent:
                        sys.stdout.write(line)
                    output += line
                else:
                    break
        while True:
            line = proc.stdout.readline().decode()
            if line:
                if not silent:
                    sys.stdout.write(line)
                output += line
            else:
                break

    if proc.poll() != 0:
        raise subprocess.CalledProcessError(proc.poll(), command)

    if strip:
        return output.strip()
    return output


def run_with_input(command, input_bytes):
    if isinstance(command, str):
        command = command.split(' ')

    options = {
        'shell': False,
        'input': input_bytes,
        'check': True,
    }
    subprocess.run(command, **options)


def copy_to_clipboard(value):
    subprocess.run(
        ['xclip', '-selection', 'clipboard'],
        input=value,
        encoding='UTF-8',
    )


def username():
    return getpass.getuser()


def home(user=None):
    if user is None:
        user = username()
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


class popd:
    def __init__(self, new_cwd):
        self.new_cwd = new_cwd
        self.old_cwd = None

    def __enter__(self):
        self.old_cwd = os.getcwd()
        os.chdir(self.new_cwd)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.old_cwd)
