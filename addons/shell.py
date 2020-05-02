import subprocess


def run(command):
    if isinstance(command, str):
        command = command.split(' ')

    returncode = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode

    if returncode != 0:
        raise NonZeroReturnCode()


def output(command):
    if isinstance(command, str):
        command = command.split(' ')

    return subprocess.check_output(command).strip().decode()


class NonZeroReturnCode(Exception):
    pass
