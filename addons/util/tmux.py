import argparse
import datetime
import glob
import os
import re
import statistics
import sys

import addons.config
import addons.helpers
import addons.shell as shell


class TmuxStatus:
    def __init__(self):
        try:
            self.config = addons.config.Config('tmux').read()
        except ValueError:
            sys.exit(0)

    def left(self):
        now = datetime.datetime.now()
        time = datetime.datetime.strftime(now, '%H:%M')
        date = datetime.datetime.strftime(now, '%A %d %B')
        print(f'#[fg=colour39]{time}', end='')
        print(f' #[fg=white]{date}  ', end='')

        charges = addons.helpers.get_battery_charges()
        mean_charge = int(statistics.mean(charges))
        if mean_charge >= 0 and mean_charge <= 15:
            print(f' #[fg=colour196]{mean_charge}% ', end='')
        elif mean_charge >= 16 and mean_charge <= 30:
            print(f' #[fg=colour208]{mean_charge}% ', end='')

        print('#[default]    ')

    def right(self):
        pm_config = addons.config.Config('packagemanager', private=False).read()
        worker_name = pm_config['users']['worker']['name']
        building = glob.glob(os.path.join(shell.home(user=worker_name), 'build*'))
        if building:
            package = re.match('^.*build\\.(.*)\\.\\d+\\..*$', building[0]).group(1)
            print(f' #[fg=colour78]{package} ', end='')

        for mailbox in self.config['watch-mailboxes']:
            path = os.path.join(self.config['mailbox-path'], mailbox['name'], 'new')
            count = len(glob.glob(os.path.join(path, '*')))
            if count > 0:
                print(' #[fg=colour{}]{} '.format(mailbox['color'], count), end='')
            else:
                print(' #[fg=colour{}]{} '.format(self.config['default-color'], count), end='')

        if shell.output('systemctl show --property=SystemState') != 'SystemState=running':
            print(' #[fg=colour196]X', end='')

        print('#[default]')

    def main(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('side', type=str)
        args = parser.parse_args()
        if args.side == 'left':
            self.left()
        elif args.side == 'right':
            self.right()


def main():
    TmuxStatus().main()


if __name__ == '__main__':
    main()
