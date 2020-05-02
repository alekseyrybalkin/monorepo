import getpass
import os
import sqlite3


def srcfetcher_test(cursor):
    cursor.execute('select 1 from project')


def srcfetcher_init(cursor):
    cursor.execute('''
        create table project(
            id integer primary key,
            name text not null,
            path text not null,
            last_attempt date,
            last_success date
        )''')
    cursor.execute('create unique index project_name_idx on project(name)')
    cursor.execute('create unique index project_path_idx on project(path)')
    cursor.execute('create index project_last_attempt_idx on project(last_attempt)')
    cursor.execute('create index project_last_success_idx on project(last_success)')


def youtube_test(cursor):
    cursor.execute('select 1 from video')


def youtube_init(cursor):
    cursor.execute('''
        create table video(
            id integer primary key,
            url text
        )''')
    cursor.execute('create index video_url on video(url)')


db_configs = {
    'srcfetcher': {
        'test': srcfetcher_test,
        'init': srcfetcher_init,
    },
    'youtube': {
        'test': youtube_test,
        'init': youtube_init,
    },
}


class DB:
    def __init__(self, name):
        self.name = name
        self.test = db_configs[name]['test']
        self.init = db_configs[name]['init']
        self.conn = None

    def __enter__(self):
        db = os.path.expanduser(
            os.path.join(
                '~{}'.format(getpass.getuser()),
                '.data',
                'databases',
                '{}.db'.format(self.name),
            ),
        )
        self.conn = sqlite3.connect(db)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        try:
            self.test(cursor)
        except sqlite3.OperationalError:
            self.init(cursor)

        self.conn.commit()
        cursor.close()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def select_one(self, sql, params=None):
        cursor = self.conn.cursor()

        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        row = cursor.fetchone()

        self.conn.commit()
        cursor.close()

        return row

    def select_many(self, sql, params=None):
        cursor = self.conn.cursor()

        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        rows = cursor.fetchall()

        self.conn.commit()
        cursor.close()

        return rows

    def execute(self, sql, params=None):
        cursor = self.conn.cursor()

        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        self.conn.commit()
        cursor.close()
