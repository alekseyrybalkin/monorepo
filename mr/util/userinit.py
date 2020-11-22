import argparse
import os

import mr.shell as shell


class UserInit:
    def __init__(self):
        self.args = self.parse_args()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('username', type=str)
        return parser.parse_args()

    def main(self):
        name = self.args.username

        max_uid = 0
        with open('/etc/passwd', 'tr') as passwd:
            for line in passwd:
                uid = int(line.split(':')[2])
                if uid > max_uid and uid < 2000:
                    max_uid = uid

        max_gid = 0
        with open('/etc/group', 'tr') as group:
            for line in group:
                gid = int(line.split(':')[2])
                if gid > max_gid and gid < 2000:
                    max_gid = gid

        new_id = max(max_uid, max_gid) + 1
        new_id = max(new_id, 1010)
        if new_id > 1999:
            raise ValueError('no free ids < 2000 left')

        shell.run('sudo groupadd --gid {} {}'.format(new_id, name))
        shell.run('sudo useradd --uid {} -m -k /dev/null -g {} -G audio,video -s /bin/bash {}'.format(
            new_id,
            name,
            name,
        ))

        if not os.path.exists(os.path.join(shell.home(user=name), '.xinitrc')):
            tmpdir = os.path.join(shell.home(user=name), 'tmp')
            shell.run('sudo -u {} git clone git://rybalkin.org/configs/dotfiles {}'.format(
                name,
                tmpdir,
            ))
            for item in os.listdir(tmpdir):
                old_path = os.path.join(tmpdir, item)
                new_path = os.path.join(shell.home(user=name), item)
                shell.run('sudo mv {} {}'.format(old_path, new_path))
            shell.run('sudo rmdir {}'.format(tmpdir))

        download_dir = os.path.join(shell.home(user=name), 'download')
        shell.run('sudo -u {} mkdir -p {}'.format(name, download_dir))


def main():
    UserInit().main()


if __name__ == '__main__':
    main()
