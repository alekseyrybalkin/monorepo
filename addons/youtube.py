import sys
import os

import requests
import youtube_dl
import lxml.etree

import addons.config
import addons.db


class YoutubeDatabase(addons.db.Database, metaclass=addons.db.DatabaseMeta):
    def exists(self, cursor):
        cursor.execute('select 1 from video')

    def create(self, cursor):
        cursor.execute('''
            create table video(
                id integer primary key,
                url text
            )''')
        cursor.execute('create index video_url on video(url)')


class VideosFetcher:
    def __init__(self, db):
        self.db = db

    def main(self):
        for ev in ('http_proxy', 'HTTP_PROXY', 'https_proxy', 'HTTPS_PROXY'):
            if ev in os.environ:
                del os.environ[ev]

        config = addons.config.Config('youtube').read()

        resps = {}
        for fmt, channels in config['fmt_channels'].items():
            for channel in channels:
                req = 'https://www.youtube.com/feeds/videos.xml?channel_id={}'.format(channel['id'])
                resps[channel['id']] = requests.get(req)
                print('.', end='')
                sys.stdout.flush()
        print()

        videos = {}
        for fmt, channels in config['fmt_channels'].items():
            videos[fmt] = []
            parser = lxml.etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
            for channel in channels:
                data = lxml.etree.fromstring(resps[channel['id']].text.encode('utf-8'), parser=parser)

                author = data.find('{http://www.w3.org/2005/Atom}author').find('{http://www.w3.org/2005/Atom}name').text
                for item in data.iterfind('{http://www.w3.org/2005/Atom}entry'):
                    title = item.find('{http://www.w3.org/2005/Atom}title').text
                    video_id = item.find('{http://www.youtube.com/xml/schemas/2015}videoId').text

                    url = 'https://www.youtube.com/watch?v={}'.format(video_id)
                    vid = self.db.select_one('select id from video where url = ?', (url,))
                    if vid is not None:
                        continue

                    user_said = ''
                    while user_said.lower() not in ['y', 'n', 'r']:
                        user_said = input('{}: {} [ {} ] (y/n/r)? '.format(author, title, url))
                    if user_said.lower() == 'y':
                        videos[fmt].append(url)
                    if user_said.lower() == 'r':
                        self.db.execute('insert into video(url) values (?)', (url,))

        for fmt in config['fmt_channels']:
            if videos[fmt]:
                opts = {
                    'format': fmt,
                }
                with youtube_dl.YoutubeDL(opts) as ydl:
                    ydl.download(videos[fmt])
                for video in videos[fmt]:
                    self.db.execute('insert into video(url) values (?)', (video,))


def fetch_videos():
    with addons.db.DB('youtube') as db:
        VideosFetcher(db).main()


if __name__ == '__main__':
    fetch_videos()
