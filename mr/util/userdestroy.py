import argparse
import os

import mr.shell as shell


class UserDestroy:
    def __init__(self):
        self.args = self.parse_args()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('username', type=str)
        return parser.parse_args()

    def main(self):
        name = self.args.username
        uid = int(shell.output('getent passwd {}'.format(name)).split(':')[2])

        if uid < 1010:
            raise ValueError('cannot destroy user with uid < 1010')

        for root, dirs, files in os.walk('/tmp'):
            for item in files:
                path = os.path.join(root, item)
                if os.stat(path).st_uid == uid:
                    shell.run('sudo rm {}'.format(path))
            for item in dirs:
                path = os.path.join(root, item)
                if os.stat(path).st_uid == uid:
                    shell.run('sudo rm -rf {}'.format(path))

        shell.run('sudo userdel {}'.format(name))
        shell.run('sudo rm -rf /home/{}'.format(name))


def main():
    UserDestroy().main()


if __name__ == '__main__':
    main()
