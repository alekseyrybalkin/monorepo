import argparse

import mr.shell as shell


class IntelBacklight:
    def __init__(self):
        self.args = self.parse_args()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('brightness', type=int)
        parser.add_argument('--sudo', action='store_true')
        return parser.parse_args()

    def main(self):
        if self.args.brightness < 1 or self.args.brightness > 100:
            raise ValueError('brightness should be between 1 and 100')

        if not self.args.sudo and shell.username() != 'root':
            shell.run('sudo python -m mr.util.intel_backlight {} --sudo'.format(self.args.brightness))
            return

        with open('/sys/class/backlight/intel_backlight/max_brightness', 'tr') as sysf:
            max_brightness = int(sysf.read().strip())

        with open('/sys/class/backlight/intel_backlight/brightness', 'tw') as sysf:
            sysf.write(str(int(self.args.brightness / 100 * max_brightness)))


def main():
    IntelBacklight().main()


if __name__ == '__main__':
    main()
