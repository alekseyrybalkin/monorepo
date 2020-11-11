import argparse
import functools
import os

import addons.config
import addons.db

config = addons.config.Config('packagemanager', private=False).read()


class PackageManagerDatabase(addons.db.Database, metaclass=addons.db.DatabaseMeta):
    def exists(self, cursor):
        cursor.execute('select 1 from package')

    def create(self, cursor):
        cursor.execute('''
            create table package(
                id integer primary key,
                name text,
                version text,
                timestamp integer
            )''')
        cursor.execute('''
            create table file(
                id integer primary key,
                package_id integer,
                permissions text,
                ownership text,
                name text,
                link text,
                is_generated integer
            )''')
        cursor.execute('''
            create table depends(
                id integer primary key,
                user_id integer,
                provider_id integer
            )''')
        cursor.execute('create index package_name on package(name)')
        cursor.execute('create index file_name on file(name)')
        cursor.execute('create index file_package_id on file(package_id)')
        cursor.execute('create index user_package_id on depends(user_id)')
        cursor.execute('create index provider_package_id on depends(provider_id)')

    def get_path(self):
        return config['db_path']


def run_as(user):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            old_egid = os.getegid()
            old_euid = os.geteuid()

            os.setegid(config['users'][user]['gid'])
            os.seteuid(config['users'][user]['uid'])
            old_umask = os.umask(config['users'][user]['umask'])

            result = func(*args, **kwargs)

            os.umask(old_umask)
            os.seteuid(old_euid)
            os.setegid(old_egid)

            return result
        return wrapper
    return decorator


class PackageManager:
    def __init__(self, db):
        self.db = db

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('action', type=str)
        return parser.parse_args()

    def main(self):
        args = self.parse_args()
        if args.action == 'ls':
            self.ls()

    @run_as('manager')
    def ls(self):
        for row in self.db.select_many('select name, version from package order by name'):
            print('{}-{}'.format(row['name'], row['version']))

    @run_as('root')
    def install(self):
        pass

    @run_as('worker')
    def make(self):
        pass


def main():
    with addons.db.DB('packagemanager') as db:
        PackageManager(db).main()


if __name__ == '__main__':
    main()
