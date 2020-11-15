import argparse

import addons.config


class HostConf:
    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('option', type=str)
        return parser.parse_args()

    def get_option(self, option):
        config = addons.config.Config('hostconf', private=False).read()
        for conf in config['hosts']:
            if conf.get('this', False):
                return conf.get(option, '')
        return ''

    def main(self):
        args = self.parse_args()
        value = self.get_option(args.option)
        if isinstance(value, list):
            for item in value:
                print(item)
        else:
            print(value)


def main():
    HostConf().main()


if __name__ == '__main__':
    main()
