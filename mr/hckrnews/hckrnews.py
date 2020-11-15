import argparse
import datetime as dt
import json
import os
import signal
import stat
import string
import sys
import time
import urllib.request

import mr.db
import mr.shell as shell

today = dt.date.today() - dt.timedelta(days=2)
tomorrow = dt.date.today() - dt.timedelta(days=1)


class HckrnewsDatabase(mr.db.Database, metaclass=mr.db.DatabaseMeta):
    def exists(self, cursor):
        cursor.execute('select 1 from day')

    def create(self, cursor):
        cursor.execute('''
            create table day(
                id text primary key,
                last_updated text
            )''')
        cursor.execute('''
            create table article(
                id integer primary key,
                link text,
                desc text,
                day text,
                points integer,
                comments integer
            )''')
        cursor.execute('create index article_day_idx on article(day)')
        cursor.execute('create index day_last_updated_idx on day(last_updated)')


class Day:
    def __init__(self, day, last_updated):
        self.day = day
        self.last_updated = last_updated


class Article:
    def __init__(self, article_id, link, desc, day, points, comments):
        self.article_id = article_id
        self.link = link
        self.desc = desc
        self.day = day
        self.points = points
        self.comments = comments


class HackerNews:
    def __init__(self, db):
        self.db = db

    def insert_day(self, day):
        self.db.execute('insert into day(id, last_updated) values (?, ?)', (day, dt.date.today()))

    def update_day(self, day):
        self.db.execute('update day set last_updated=? where id=?', (dt.date.today(), day))

    def get_day(self, day):
        return self.db.select_one(
            'select id, last_updated from day where id = ?',
            (day,),
            Day,
        )

    def insert_article(self, article_id, link, desc, day, points, comments):
        self.db.execute(
            '''
                insert into article(id, link, desc, day, points, comments)
                    values (?, ?, ?, ?, ?, ?)
            ''',
            (article_id, link, desc, day, points, comments),
        )

    def update_article(self, article_id, points, comments):
        self.db.execute('update article set points=?, comments=? where id=?', (points, comments, article_id))

    def get_article(self, article_id):
        return self.db.select_one(
            '''
                select id, link, desc, day, points, comments
                    from article
                    where id = ?
            ''',
            (article_id,),
            Article,
        )

    def get_articles(self, date_start, date_end):
        return self.db.select_many(
            '''
                select id, link, desc, day, points, comments
                    from article
                    where day >= ? and day < ?
            ''',
            (date_start, date_end),
            Article,
        )

    def select_days_for_update(self, num_days=10):
        rows = self.db.select_many(
            'select id, last_updated from day where id >= ?',
            (today - dt.timedelta(days=num_days),),
        )
        all_days = set(today - dt.timedelta(days=x) for x in range(num_days))
        skip = set()
        for d in rows:
            day = dt.datetime.strptime(d['id'], '%Y-%m-%d').date()
            last_updated = dt.datetime.strptime(d['last_updated'], '%Y-%m-%d').date()
            if last_updated - day >= dt.timedelta(days=7) or last_updated >= dt.date.today():
                skip.add(day)
        return sorted(list(all_days - skip))

    def update_day_from_hckrnews(self, day, quiet):
        url = 'https://hckrnews.com/data/{}.js'.format(day.strftime('%Y%m%d'))
        if not quiet:
            print('fetching {}...'.format(url))
        with urllib.request.urlopen(url) as req:
            stories = json.loads(req.read())

        if self.get_day(day) is None:
            self.insert_day(day)
        else:
            self.update_day(day)

        for a in stories:
            try:
                int(a['id'])
            except ValueError:
                continue

            if self.get_article(a['id']) is None:
                self.insert_article(a['id'], a['link'], a['link_text'], day, a['points'], a['comments'])
            else:
                self.update_article(a['id'], a['points'], a['comments'])

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('action', type=str, help='update, month or full')
        parser.add_argument('param', type=str, nargs='?', help='%Y.%m for month')
        parser.add_argument('--quiet', action='store_true')
        parser.add_argument('--all', action='store_true')
        parser.add_argument('--html', action='store_true')
        args = parser.parse_args()

        if args.action != 'update' and args.action != 'full' and args.param is None:
            print('{} requires param'.format(args.action))
            sys.exit(0)

        return args.action, args.param, args.quiet, args.all, args.html

    def main(self):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

        # don't die when stopped, try to finish your job first
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        articles = []

        action, param, quiet, show_all, html = self.parse_args()

        if action == 'update':
            # hckrnews data starts from 2010.06.09, calc the max number like so:
            # (dt.date.today() - dt.date(2010, 6, 9)).days - 1
            for day in self.select_days_for_update(num_days=1652):
                try:
                    self.update_day_from_hckrnews(day, quiet)
                except (IOError, ValueError):
                    break
                time.sleep(2)
        elif action == 'full':
            articles = self.get_articles(dt.date(1990, 1, 1), dt.date(3000, 1, 1))
        elif action == 'month':
            # allow only once in a month, on a second sunday
            now = dt.datetime.now()
            if now.weekday() != 6 or (now.day - 1) // 7 != 1:
                print('Today is not a second sunday of the month. Bye.')
                sys.exit(0)

            date_from = dt.datetime.strptime(param, '%Y.%m').date()
            if date_from.month < 12:
                date_to = dt.datetime(date_from.year, date_from.month + 1, 1).date()
            else:
                date_to = dt.datetime(date_from.year + 1, 1, 1).date()
            articles = self.get_articles(date_from, date_to)

        if html:
            template_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'newsitem.html')
            template = string.Template(open(template_file, 'tr').read())
            with open('/tmp/hckrnews.html', 'tw') as html_file:
                html_file.write('<body style="margin: 30px;">')
                for article in sorted(articles, key=lambda x: (x.points or 0, x.comments or 0)):
                    if (show_all and (article.points or 0) >= 10) or (not show_all and (article.points or 0) >= 500):
                        html_file.write(template.substitute(
                            points=article.points or '',
                            description=article.desc[:150],
                            article_link=article.link,
                            hn_link='https://news.ycombinator.com/item?id={}'.format(article.article_id),
                            comments=article.comments,
                        ))
                html_file.write('</body>')
            os.chmod('/tmp/hckrnews.html', stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        else:
            for article in sorted(articles, key=lambda x: (x.points or 0, x.comments or 0)):
                if (show_all and (article.points or 0) >= 10) or (not show_all and (article.points or 0) >= 500):
                    print('{:<6}{:<150}'.format(article.points or '', article.desc[:150]))
                    print('          {}'.format(article.link))
                    print('          https://news.ycombinator.com/item?id={}'.format(article.article_id))
                    print('          comments: {}'.format(article.comments))


def main():
    with mr.db.DB('hckrnews') as db:
        HackerNews(db).main()


if __name__ == '__main__':
    main()
