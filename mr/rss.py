import argparse
import datetime
import os
import urllib.request
import xml.etree.ElementTree as ET

import mr.config
import mr.db
import mr.shell as shell


class RSSDatabase(mr.db.Database, metaclass=mr.db.DatabaseMeta):
    def exists(self, cursor):
        cursor.execute('select 1 from feed')

    def create(self, cursor):
        cursor.execute('''
            create table feed(
                id text primary key,
                last_updated date
            )''')
        cursor.execute('''
            create table article(
                link text primary key,
                feed_id integer,
                title text,
                description text,
                pub_date date,
                read integer
            )''')
        cursor.execute('create index feed_last_updated_idx on feed(last_updated)')
        cursor.execute('create index article_feed_id_idx on article(feed_id)')
        cursor.execute('create index article_read_idx on article(read)')
        cursor.execute('create index article_pub_date_idx on article(pub_date)')


class RSSReader:
    def __init__(self, db):
        self.db = db
        self.args = self.parse_args()
        self.config = mr.config.Config('rss').read()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('action', type=str, default='read', nargs='?')
        return parser.parse_args()

    def main(self):
        if self.args.action == 'read':
            for article in self.db.select_many('select * from article where read = 0 order by feed_id, pub_date'):
                os.system('clear')
                print(article['pub_date'])
                print(article['link'])
                print()
                print('  ' + shell.colorize(article['title'], color=2))
                print()
                print(article['description'])
                print()
                user_said = 'x'
                while user_said.lower() not in ['y', 'n', '']:
                    user_said = input('Mark as read (Y/n)? ')
                if user_said.lower() != 'n':
                    self.db.execute(
                        'update article set read = 1 where link = ? and feed_id = ?',
                        (article['link'], article['feed_id']),
                    )
        if self.args.action == 'fetch':
            for feed in self.config['feeds']:
                db_feed = self.db.select_one('select * from feed where id = ?', (feed['name'],))
                if not db_feed:
                    self.db.execute(
                        'insert into feed(id, last_updated) values(?, ?)',
                        (feed['name'], '1970-01-01 00:00:00.000000'),
                    )
                    db_feed = self.db.select_one('select * from feed where id = ?', (feed['name'],))

                last_updated = datetime.datetime.strptime(db_feed['last_updated'], '%Y-%m-%d %H:%M:%S.%f')
                if (datetime.datetime.now() - last_updated).total_seconds() // 60 < self.config['interval_minutes']:
                    continue

                with urllib.request.urlopen(feed['url']) as req:
                    root = ET.fromstring(req.read())

                for item in root.findall(feed['items_xpath']):
                    title = item.find(feed['title_tag']).text
                    link = item.find(feed['link_tag']).text
                    description = item.find(feed['description_tag']).text
                    date = datetime.datetime.strptime(
                        item.find(feed['date_tag']).text,
                        feed['date_format'],
                    )
                    db_article = self.db.select_one(
                        'select * from article where link = ? and feed_id = ?',
                        (link, db_feed['id']),
                    )
                    if not db_article:
                        self.db.execute(
                            '''
                                insert into article (link, feed_id, title, description, pub_date, read)
                                    values (?, ?, ?, ?, ?, 0)
                            ''',
                            (link, db_feed['id'], title, description, date),
                        )


def main():
    with mr.db.DB('rss') as db:
        RSSReader(db).main()


if __name__ == '__main__':
    main()
