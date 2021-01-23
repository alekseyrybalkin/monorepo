import datetime as dt
import os
import time
import urllib.request
import xml.etree.ElementTree as ET

import mr.config
import mr.shell as shell


class Videos:
    def __init__(self):
        self.config = mr.config.Config('videos').read()

    def main(self):
        platform_cfg = {
            'youtube': {
                'find_entry': lambda e: e.findall('{http://www.w3.org/2005/Atom}entry')[:self.config['max_vids']],
                'find_date': lambda e: e.find('{http://www.w3.org/2005/Atom}published').text,
                'convert_date': lambda s: dt.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S+00:00').strftime('%Y-%m-%d'),
                'find_title': lambda e: e.find('{http://www.w3.org/2005/Atom}title').text,
                'find_link': lambda e: e.find('{http://www.w3.org/2005/Atom}link').attrib['href'],
            },
            'twitch': {
                'find_entry': lambda e: e.find('channel').findall('item')[:self.config['max_vids']],
                'find_date': lambda e: e.find('pubDate').text,
                'convert_date': lambda s: dt.datetime.strptime(s, '%a, %d %b %Y %H:%M:%S UT').strftime('%Y-%m-%d'),
                'find_title': lambda e: e.find('title').text,
                'find_link': lambda e: e.find('link').text,
            },
        }

        for platform in ['youtube', 'twitch']:
            for channel in self.config[platform]['channels']:
                print(shell.colorize(channel['name'], color=2))

                with urllib.request.urlopen(self.config[platform]['url'].format(channel['id'])) as req:
                    raw = req.read().decode()
                    time.sleep(1.0)

                for entry in platform_cfg[platform]['find_entry'](ET.fromstring(raw)):
                    date = platform_cfg[platform]['convert_date'](platform_cfg[platform]['find_date'](entry))
                    print('    {{:<14}}{{:<{}}}{{}}'.format(self.config['title_length']).format(
                        date,
                        platform_cfg[platform]['find_title'](entry)[:(self.config['title_length'] - 4)],
                        platform_cfg[platform]['find_link'](entry),
                    ))

                print()


def main():
    Videos().main()


if __name__ == '__main__':
    main()
