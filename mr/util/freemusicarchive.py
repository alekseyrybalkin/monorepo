import argparse
import os
import random
import re
import urllib.request


class FreeMusicArchive:
    def __init__(self):
        self.args = self.parse_args()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('action', type=str)
        parser.add_argument('url', type=str)
        return parser.parse_args()

    def fetch(self, url):
        print(f'downloading {url}')
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'random/0.6210048391254004'},
        )
        with urllib.request.urlopen(req) as oreq:
            return oreq.read()

    def get_song_list(self, html):
        song_url_re = re.compile(':"(https[^"]*\\.mp3)"')
        return list(url.replace('\\/', '/') for url in song_url_re.findall(html))

    def download(self, url, peek=False):
        album = os.path.basename(url)
        artist = os.path.basename(os.path.dirname(url))
        path = '{}.{}'.format(artist, album)
        os.makedirs(path, exist_ok=True)

        song_list_path = os.path.join(path, 'song_list.txt')

        if os.path.exists(song_list_path):
            with open(song_list_path, 'tr') as sl_file:
                song_list = sl_file.read().strip().split('\n')
        else:
            html = self.fetch(url).decode()
            song_list = self.get_song_list(html)
            with open(song_list_path, 'tw') as sl_file:
                for song in song_list:
                    sl_file.write(song + '\n')

        if peek:
            song_list = [random.choice(song_list)]

        for song_url in song_list:
            song = os.path.basename(song_url)

            song_path = os.path.join(path, song)
            if not os.path.exists(song_path):
                with open(song_path, 'bw') as song_file:
                    song_file.write(self.fetch(song_url))

    def main(self):
        if self.args.action == 'download':
            self.download(self.args.url)
        elif self.args.action == 'peek':
            self.download(self.args.url, peek=True)


def main():
    FreeMusicArchive().main()


if __name__ == '__main__':
    main()
