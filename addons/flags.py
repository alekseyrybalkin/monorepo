import argparse
import getpass
import os
import re

flagsrc = os.path.expanduser(
    os.path.join(
        '~{}'.format(getpass.getuser()),
        '.config',
        'flagsrc',
    )
)

default_flags = {
    'tmux_mail': True,
}


class Flags:
    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-n', type=str, required=True, help='flag name')
        parser.add_argument('-s', type=str, required=True, help='state: on/off')
        args = parser.parse_args()

        assert args.n in default_flags, 'unknown flag {}'.format(args.n)
        assert args.s in ('on', 'off'), 'unknown state {}, should be on/off'.format(args.s)

        return args.n, args.s == 'on'

    def read_rc_flags(self):
        rc_flags = {}
        if os.path.exists(flagsrc):
            with open(flagsrc, 'tr') as f:
                for flag_def in f:
                    flag, value = (v.strip() for v in flag_def.split('='))
                    assert flag.startswith('flag_')
                    flag = re.sub('^flag_', '', flag)
                    assert flag in default_flags
                    assert value in ('on', 'off')
                    rc_flags[flag] = (value == 'on')
        return rc_flags

    def write_rc_flags(self, rc_flags):
        with open(flagsrc, 'tw') as f:
            for flag, value in rc_flags.items():
                f.write('flag_{}={}\n'.format(flag, 'on' if value else 'off'))

    def main(self):
        name, state = self.parse_args()

        flags = default_flags
        flags.update(self.read_rc_flags())
        flags[name] = state

        self.write_rc_flags(flags)


def main():
    Flags().main()


if __name__ == '__main__':
    main()
