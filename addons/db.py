import os
import sqlite3

import addons.shell as shell

db_registry = {}


class DatabaseMeta(type):
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        name = cls.__name__.replace('Database', '').lower()
        cls.name = name
        db_registry[name] = cls
        return cls


class Database:
    name = 'default'

    def exists(self, cursor):
        return True

    def create(self, cursor):
        pass

    def get_path(self):
        return os.path.join(shell.home(), '.data', 'databases', '{}.db'.format(self.name))


class DB:
    def __init__(self, name):
        self.db_manager = db_registry[name]()
        self.db = self.db_manager.get_path()
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        try:
            self.db_manager.exists(cursor)
        except sqlite3.OperationalError:
            self.db_manager.create(cursor)

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

    def executemany(self, sql, params):
        cursor = self.conn.cursor()

        cursor.executemany(sql, params)

        self.conn.commit()
        cursor.close()
