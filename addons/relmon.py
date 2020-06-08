#!/usr/bin/env python

import argparse
import datetime
import json
import signal
import time

import requests

import addons.db


class Relmon:
    def __init__(self, db):
        self.db = db

    def get_by_id(self, package_id):
        url = 'https://release-monitoring.org/api/project/{}'
        return requests.get(url.format(package_id)).json()

    def search_by_name(self, name):
        url = 'https://release-monitoring.org/api/projects/?pattern={}'
        return requests.get(url.format(name)).json()

    def get_from_cache(self, package_id):
        row = self.db.select_one('select info from package where id = ?', (package_id,))
        if not row or not row['info']:
            return None
        return json.loads(row['info'])

    def update_cached(self, package_id, info):
        now = datetime.datetime.now()
        self.db.execute(
            '''
                insert into package(id, info, updated)
                    values (?, ?, ?)
                    on conflict(id) do
                    update set info = ?, updated = ?
            ''',
            (int(package_id), json.dumps(info), now, json.dumps(info), now),
        )

    def add_cached_placeholder(self, package_id):
        old_date = datetime.datetime(1970, 1, 1)
        self.db.execute(
            '''
                insert into package(id, info, updated)
                    values (?, ?, ?)
                    on conflict(id) do
                    update set updated = ?
            ''',
            (int(package_id), None, old_date, old_date),
        )

    def get_oldest_expired(self):
        prev_date = datetime.datetime.now() - datetime.timedelta(days=2)
        return self.db.select_one(
            'select id from package where updated <= ? order by updated asc limit 1',
            (prev_date,),
        )

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
                        info = self.get_by_id(package['id'])
                        self.update_cached(package['id'], info)
                        time.sleep(2.0)


def main():
    with addons.db.DB('relmon') as db:
        Relmon(db).main()


if __name__ == '__main__':
    main()
