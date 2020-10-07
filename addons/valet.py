import datetime
import functools
import json
import signal
import sys
import os
import argparse
import glob
import time

import addons.db


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

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('day', type=int, default=0, nargs='?')
        parser.add_argument('--toggle-done', type=int, default=-1)
        parser.add_argument('--email', action='store_true')
        args = parser.parse_args()

        day = datetime.date.today() + datetime.timedelta(days=args.day)
        return day, args.toggle_done, args.email

    def main(self):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

        routines = []

        with open('/home/rybalkin/.config/private/valet.json', 'tr') as conffile:
            config = json.loads(conffile.read())
            for group in config['routines']:
                routines.extend([Routine(**item) for item in config['routines'][group]])

        day, toggle_done, email = self.parse_args()

        tasks = sorted([r.get_text(day) for r in routines if r.check_day(day)])

        # cleanup
        sometime_ago = datetime.date.today() - datetime.timedelta(days=30)
        self.db.execute('delete from done where day < ?', (sometime_ago,))

        if toggle_done >= 0:
            task = tasks[toggle_done]
            item = self.db.select_one('select id from done where day = ? and task = ?', (day, task))
            print(item)
            if self.db.select_one('select id from done where day = ? and task = ?', (day, task)):
                self.db.execute('delete from done where day = ? and task = ?', (day, task))
            else:
                self.db.execute('insert into done(day, task) values (?, ?)', (day, task))

        done = set(row['task'] for row in self.db.select_many('select task from done where day = ?', (day,)))
        print(done)

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


def main():
    with addons.db.DB('valet') as db:
        Valet(db).main()


if __name__ == '__main__':
    main()
