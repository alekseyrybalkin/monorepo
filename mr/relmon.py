import argparse
import datetime
import json
import logging
import signal
import time
import urllib.request

import mr.db


class RelmonDatabase(mr.db.Database, metaclass=mr.db.DatabaseMeta):
    def exists(self, cursor):
        cursor.execute('select 1 from package')

    def create(self, cursor):
        cursor.execute('''
            create table package(
                id integer primary key,
                info text,
                last_attempt date,
                last_success date
            )''')
        cursor.execute('create index package_last_attempt_idx on package(last_attempt)')
        cursor.execute('create index package_last_success_idx on package(last_success)')


class Relmon:
    def __init__(self, db):
        self.db = db

    def get_by_id(self, package_id):
        url = 'https://release-monitoring.org/api/project/{}'
        with urllib.request.urlopen(url.format(package_id)) as req:
            return json.loads(req.read())

    def search_by_name(self, name):
        url = 'https://release-monitoring.org/api/projects/?pattern={}'
        with urllib.request.urlopen(url.format(name)) as req:
            return json.loads(req.read())

    def get_from_cache(self, package_id):
        row = self.db.select_one('select info from package where id = ?', (package_id,))
        if not row or not row['info']:
            return None
        return json.loads(row['info'])

    def update_cached(self, package_id, info, success=True):
        now = datetime.datetime.now()
        if success:
            self.db.execute(
                '''
                    insert into package(id, info, last_attempt, last_success)
                        values (?, ?, ?, ?)
                        on conflict(id) do
                        update set info = ?, last_attempt = ?, last_success = ?
                ''',
                (int(package_id), json.dumps(info), now, now, json.dumps(info), now, now),
            )
        else:
            old_date = datetime.datetime(1970, 1, 1)
            self.db.execute(
                '''
                    insert into package(id, last_attempt, last_success)
                        values (?, ?, ?)
                        on conflict(id) do
                        update set last_attempt = ?
                ''',
                (int(package_id), now, old_date, now),
            )

    def add_cached_placeholder(self, package_id):
        old_date = datetime.datetime(1970, 1, 1)
        self.db.execute(
            '''
                insert into package(id, info, last_attempt, last_success)
                    values (?, ?, ?, ?)
                    on conflict(id) do
                    update set last_attempt = ?, last_success = ?
            ''',
            (int(package_id), None, old_date, old_date, old_date, old_date),
        )

    def get_oldest_expired(self):
        prev_date = datetime.datetime.now() - datetime.timedelta(days=2)
        return self.db.select_one(
            '''
                select id from package
                    where last_attempt is null or last_attempt <= ?
                    order by last_attempt asc
                    limit 1
            ''',
            (prev_date,),
        )

    def get_all_failed(self):
        return self.db.select_many('select id from package where last_success <> last_attempt')

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('query', type=str, nargs='?')
        parser.add_argument('--cached', action='store_true')
        parser.add_argument('--update', action='store_true')
        args = parser.parse_args()

        return args.query, args.cached, args.update

    def get_all_packages(self):
        return self.db.select_many('select * from package')

    def main(self):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        # don't die when stopped, try to finish your job first
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        query, cached, update = self.parse_args()

        if query:
            if query.isdigit():
                if not cached:
                    info = self.get_by_id(query)
                    self.update_cached(query, info)
                    cached_info = self.get_from_cache(query)
                    if not cached_info:
                        self.add_cached_placeholder(query)
                else:
                    if update:
                        info = self.get_by_id(query)
                        self.update_cached(query, info)
                    info = self.get_from_cache(query)
                    if not info:
                        self.add_cached_placeholder(query)
                print(json.dumps(info, indent=4))
            else:
                if update:
                    print('update not implemented for name queries')
                    return
                if not cached:
                    info = self.search_by_name(query)
                    for i, project in enumerate(info['projects']):
                        if i > 0:
                            print()
                        print(project['name'])
                        print('  id = {}'.format(project['id']))
                        print('  version = {}'.format(project['version']))
                        print('  url = {}'.format(project['homepage']))
                else:
                    print('no cache for name queries')
        else:
            if update and not cached:
                for i in range(3):
                    package = self.get_oldest_expired()
                    if package:
                        success = True
                        info = None
                        try:
                            info = self.get_by_id(package['id'])
                        except Exception as e:
                            success = False
                            logging.error(str(e))
                        self.update_cached(package['id'], info, success)
                        time.sleep(2.0)


def main():
    with mr.db.DB('relmon') as db:
        Relmon(db).main()


if __name__ == '__main__':
    main()
