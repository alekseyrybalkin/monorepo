import os.path
import subprocess
import time

import addons.shell as shell


def main():
    timestamp = str(int(time.time()))
    file_path = os.path.join(os.path.expanduser('~'), '{}.png'.format(timestamp))
    try:
        import mss
        with mss.mss() as screen:
            screen.shot(output=file_path)
    except ModuleNotFoundError:
        shell.run(['maim', str(file_path)])
