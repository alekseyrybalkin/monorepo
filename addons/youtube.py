import sys
import os

import requests
import youtube_dl
import lxml.etree

import addons.db

channels = [
    'UCDYZxJE8kLZ-o6nL8E1bXdQ',  # MATN
    'UCKab3hYnOoTZZbEUQBMx-ww',  # NerdCubed
    'UCNUfNaego-snWXd8vygfpAg',  # sprEEEzy
    'UC7-E5xhZBZdW-8d7V80mzfg',  # JennyENicholson
    'UC-lHJZR3Gqxm24_Vd_AJ5Yw',  # PewDiePie
    'UCOpcACMWblDls9Z6GERVi1A',  # Screen Junkies
    'UCf6J9yokPS0ys456jvjLBGQ',  # Fandom Games
    'UCbiOAho0h23IMInURiESx1w',  # Dan Murrell
]


class VideosFetcher:
    def __init__(self, db):
        self.db = db

    def main(self):
        for ev in ('http_proxy', 'HTTP_PROXY', 'https_proxy', 'HTTPS_PROXY'):
            if ev in os.environ:
                del os.environ[ev]

        resps = {}
        for channel in channels:
            req = 'https://www.youtube.com/feeds/videos.xml?channel_id={}'.format(channel)
            resps[channel] = requests.get(req)
            print('.', end='')
            sys.stdout.flush()
        print()

        videos = []
        parser = lxml.etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        for channel in channels:
            data = lxml.etree.fromstring(resps[channel].text.encode('utf-8'), parser=parser)

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
                    videos.append(url)
                if user_said.lower() == 'r':
                    self.db.execute('insert into video(url) values (?)', (url,))

        if videos:
            opts = {
                'format': '299+140/137+140/best',
            }
            with youtube_dl.YoutubeDL(opts) as ydl:
                ydl.download(videos)
            for video in videos:
                self.db.execute('insert into video(url) values (?)', (video,))


def fetch_videos():
    with addons.db.DB('youtube') as db:
        VideosFetcher(db).main()
