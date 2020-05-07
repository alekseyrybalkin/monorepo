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


def hckrnews_test(cursor):
    cursor.execute('select 1 from day')


def hckrnews_init(cursor):
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


def relmon_test(cursor):
    cursor.execute('select 1 from package')


def relmon_init(cursor):
    cursor.execute('''
        create table package(
            id integer primary key,
            info text,
            updated date
        )''')
    cursor.execute('create index package_updated_idx on package(updated)')


db_configs = {
    'srcfetcher': {
        'test': srcfetcher_test,
        'init': srcfetcher_init,
    },
    'hckrnews': {
        'test': hckrnews_test,
        'init': hckrnews_init,
        'path': os.path.expanduser(
            os.path.join(
                '~{}'.format(getpass.getuser()),
                '.data',
                'databases',
                'large',
                'hckrnews.db',
            ),
        ),
    },
    'relmon': {
        'test': relmon_test,
        'init': relmon_init,
    },
}


class DB:
    def __init__(self, name):
        self.name = name
        self.test = db_configs[name]['test']
        self.init = db_configs[name]['init']
        self.conn = None
        if 'path' in db_configs[name]:
            self.db = db_configs[name]['path']
        else:
            self.db = self.get_default_db()

    def get_default_db(self):
        return os.path.expanduser(
            os.path.join(
                '~{}'.format(getpass.getuser()),
                '.data',
                'databases',
                '{}.db'.format(self.name),
            ),
        )

    def __enter__(self):
        self.conn = sqlite3.connect(self.db)
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

    def select_one(self, sql, params=None, model=None):
        cursor = self.conn.cursor()

        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        row = cursor.fetchone()

        self.conn.commit()
        cursor.close()

        if model is not None:
            return model(*row) if row is not None else None
        return row

    def select_many(self, sql, params=None, model=None):
        cursor = self.conn.cursor()

        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        rows = cursor.fetchall()

        self.conn.commit()
        cursor.close()

        if model is not None and rows:
            return [model(*row) for row in rows]
        return rows

    def execute(self, sql, params=None):
        cursor = self.conn.cursor()

        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        self.conn.commit()
        cursor.close()
