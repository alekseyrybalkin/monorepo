import argparse

import addons.config


class HostConf:
    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('option', type=str, default='label', nargs='?')
        return parser.parse_args()

    def main(self):
        args = self.parse_args()
        config = addons.config.Config('hostconf', private=False).read()

        with open(config['label-file'], 'tr') as label_file:
            label = label_file.read().strip()

        if args.option == 'label':
            print(label)
        else:
            print(config['hosts'][label][args.option])


def main():
    HostConf().main()


if __name__ == '__main__':
    main()
