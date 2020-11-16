import argparse
import os
import random

import mr.config
import mr.shell as shell


class Browser:
    def __init__(self):
        self.args = self.parse_args()
        self.config = mr.config.Config('browser', private=False).read()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('kind', type=str)
        parser.add_argument('--incognito', action='store_true')
        return parser.parse_args()

    def main(self):
        for key, val in self.config['env'].items():
            os.environ[key] = val.format(user=shell.user())

        rnd_user_agent = 'random/{}'.format(random.random())

        opts = self.config['opts']
        opts.update({
            'incognito': '--incognito' if self.args.incognito else '',
            'rnd_user_agent': rnd_user_agent,
            'home': shell.home(),
        })

        rule = self.config['rules'][self.args.kind]
        command = []
        for part in rule:
            command.append(part.format(**opts))
        shell.run(command)


def main():
    Browser().main()


if __name__ == '__main__':
    main()
