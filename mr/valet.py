import argparse
import datetime
import functools
import glob
import json
import os
import signal
import sys
import time

import mr.config
import mr.db


class ValetDatabase(mr.db.Database, metaclass=mr.db.DatabaseMeta):
    def exists(self, cursor):
        cursor.execute('select 1 from done')

    def create(self, cursor):
        cursor.execute('''
            create table done(
                id integer primary key,
                day text,
                task text
            )''')
        cursor.execute('create index done_idx on done(day, task)')


class Routine:
    def __init__(self, name, date=None, year=None, month=None, day_of_month=None, day_of_week=None,
                 day_mod=None, day_mod_shift=None, until=None, skip_weekends=False, day_of_week_in_a_month=None):
        self.name = name

        self.year = year
        if year and not isinstance(year, list):
            self.year = [year]
        self.month = month
        if month and not isinstance(month, list):
            self.month = [month]
        self.day_of_month = day_of_month
        if day_of_month and not isinstance(day_of_month, list):
            self.day_of_month = [day_of_month]

        if date:
            date = datetime.datetime.strptime(date, '%d.%m.%Y')
            self.year = [date.year]
            self.month = [date.month]
            self.day_of_month = [date.day]

        self.day_of_week = day_of_week
        if day_of_week and not isinstance(day_of_week, list):
            self.day_of_week = [day_of_week]
        self.day_of_week_in_a_month = day_of_week_in_a_month
        self.day_mod = day_mod
        self.day_mod_shift = day_mod_shift
        self.until = until
        self.skip_weekends = skip_weekends

    def get_text(self, day):
        if isinstance(self.name, str):
            return self.name
        return self.name(day)

    def check_day(self, day):
        if self.year is not None:
            if day.year not in self.year:
                return False
        if self.month is not None:
            if day.month not in self.month:
                return False
        if self.day_of_month is not None:
            if day.day not in self.day_of_month:
                return False
        if self.day_mod is not None:
            shift = self.day_mod_shift or 0
            if ((int(day.strftime('%s')) - 1) // 86400 - shift) % self.day_mod != 0:
                return False
        if self.day_of_week is not None:
            if day.isoweekday() not in self.day_of_week:
                return False
            if self.day_of_week_in_a_month is not None:
                if self.day_of_week_in_a_month == -1:
                    if (day + datetime.timedelta(days=7)).month == day.month:
                        return False
                else:
                    day_index = (day.day - 1) // 7
                    if day_index != self.day_of_week_in_a_month:
                        return False
        if self.skip_weekends:
            if day.isoweekday() in (6, 7):
                return False
        if self.until is not None:
            days = (day - datetime.date(1986, 2, 27)).days
            if days > self.until:
                return False
        return True


class Valet:
    def __init__(self, db):
        self.db = db

    def color_print(self, text, color=7, override=False):
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty() and not override:
            seq = "\x1b[1;{}m".format(30 + color) + text + "\x1b[0m\n"
            sys.stdout.write(seq)
        else:
            sys.stdout.write(text + '\n')

    def parse_args(self, toggle_done):
        parser = argparse.ArgumentParser()
        if toggle_done:
            parser.add_argument('toggle', type=int, default=0, nargs='?')
        parser.add_argument('day', type=int, default=0, nargs='?')
        parser.add_argument('--email', action='store_true')
        return parser.parse_args()

    def main(self, toggle_done):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        day, tasks, done, email = self.get_data(toggle_done)

        indent = '' if email else ' ' * 4
        if not email:
            os.system('clear')
        print()
        self.color_print('{}{}'.format(indent, day.strftime('%d.%m.%Y  %A')), 7, email)
        print()
        for i, r in enumerate(tasks):
            self.color_print(
                '{}   {:>2d} [{}] '.format(indent, i, 'v' if r in done else ' ') + r,
                2 if r in done else 7,
                email,
            )
        print()

    def get_data(self, toggle_done):
        routines = []

        config = mr.config.Config('valet').read()
        for group in config['routines']:
            routines.extend([Routine(**item) for item in config['routines'][group]])

        args = self.parse_args(toggle_done)
        day = datetime.date.today() + datetime.timedelta(days=args.day)

        tasks = sorted([r.get_text(day) for r in routines if r.check_day(day)])

        # cleanup
        sometime_ago = datetime.date.today() - datetime.timedelta(days=30)
        self.db.execute('delete from done where day < ?', (sometime_ago,))

        if toggle_done and args.toggle >= 0:
            task = tasks[args.toggle]
            item = self.db.select_one('select id from done where day = ? and task = ?', (day, task))
            if self.db.select_one('select id from done where day = ? and task = ?', (day, task)):
                self.db.execute('delete from done where day = ? and task = ?', (day, task))
            else:
                self.db.execute('insert into done(day, task) values (?, ?)', (day, task))

        done = set(row['task'] for row in self.db.select_many('select task from done where day = ?', (day,)))

        return day, tasks, done, args.email


def just_show():
    with mr.db.DB('valet') as db:
        Valet(db).main(toggle_done=False)


def toggle_done_and_show():
    with mr.db.DB('valet') as db:
        Valet(db).main(toggle_done=True)


if __name__ == '__main__':
    just_show()
