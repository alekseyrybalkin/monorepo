import argparse
import os

import mr.shell as shell
import mr.util.hostconf


class Dotfiles:
    def __init__(self):
        self.args = self.parse_args()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('action', type=str)
        return parser.parse_args()

    def main(self):
        chroot_root = '/.{}/root'.format(mr.util.hostconf.HostConf().get_option('chroot'))

        shell.run('sudo systemctl stop iptables')
        homes = [os.path.join('/home', user) for user in os.listdir('/home')]

        for place in homes + ['/root', chroot_root]:
            print(shell.colorize('[{}]'.format(place), color=2))
            user = os.path.basename(place)
            shell.run('sudo -u {} git --git-dir={}/.git --work-tree={} {}'.format(
                user,
                place,
                place,
                self.args.action,
            ))
        shell.run('sudo systemctl start iptables')

        print(shell.colorize('[cloud:aleksey]', color=2))
        shell.run([
            'ssh',
            os.environ['CLOUD'],
            'git --git-dir=/home/aleksey/.git --work-tree=/home/aleksey {}'.format(self.args.action),
        ])
        print(shell.colorize('[cloud:housecarl]', color=2))
        shell.run([
            'ssh',
            os.environ['CLOUD'],
            'sudo -u housecarl git --git-dir=/home/housecarl/.git --work-tree=/home/housecarl {}'.format(
                self.args.action,
            ),
        ])
        print(shell.colorize('[cloud:root]', color=2))
        shell.run([
            'ssh',
            os.environ['CLOUD'],
            'sudo git --git-dir=/root/.git --work-tree=/root {}'.format(self.args.action),
        ])


def main():
    Dotfiles().main()


if __name__ == '__main__':
    main()
