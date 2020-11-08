import argparse
import os
import random

import addons.config


class ChromiumThemeGenerator:
    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('name', type=str)
        return parser.parse_args()

    def main(self):
        args = self.parse_args()

        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)

        configs_path = addons.config.Config('common').read()['configs-path']
        theme_dir = os.path.join(configs_path, 'usr/lib/chromium/themes/{}'.format(args.name))
        os.makedirs(theme_dir, exist_ok=True)
        theme_file_path = os.path.join(theme_dir, 'manifest.json')

        with open(theme_file_path, 'tw') as theme_file:
            theme_file.write(
                '''
{{
    "manifest_version": 2,
    "theme": {{
        "colors": {{
            "frame_incognito":[{red}, {green}, {blue}],
            "frame":[{red}, {green}, {blue}]
        }}
    }},
    "name":"chromium-{name}",
    "version":"1",
    "description":""
}}
                '''.format(red=red, green=green, blue=blue, name=args.name).strip() + '\n',
            )


def main():
    ChromiumThemeGenerator().main()


if __name__ == '__main__':
    main()
