'''
TODO
- db locking
'''
import argparse
import functools
import os

import addons.config
import addons.db
import addons.ji.integrity as integrity
import addons.ji.make as make
import addons.ji.queries as queries
import addons.ji.sources as sources
import addons.ji.tarball as tarball

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


actions = {}


def run_as(user):
    def decorator(func):
        actions[func.__name__] = func

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
        self.config = config
        self.args = self.parse_args()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('action', type=str)
        parser.add_argument('param', type=str, nargs="*")
        return parser.parse_args()

    def setup(self):
        for key, val in self.config['env'].items():
            os.environ[key] = val

    def do_action(self):
        action_aliases = {
            'l': 'links-both',
            'u': 'upgrade-rebuild',
        }
        action = self.args.action
        action = action_aliases.get(action, action)

        actions[action.replace('-', '_')](self)

    def main(self):
        self.setup()
        self.do_action()

    @run_as('manager')
    def prepare(self):
        make.prepare(self)

    @run_as('root')
    def make(self):
        make.make(self)

    @run_as('worker')
    def make_worker(self):
        make.make_worker(self)

    @run_as('manager')
    def download(self):
        tarball.download(self)

    @run_as('root')
    def gen_db(self):
        lib.gen_db(self)

    @run_as('manager')
    def who_owns(self):
        lib.who_owns(self)

    @run_as('manager')
    def who_uses_dir(self):
        for item in queries.who_uses_dir(self, self.args.param[0]):
            print(item)

    @run_as('manager')
    def check_conflicts(self):
        lib.check_conflicts(self)

    @run_as('manager')
    def list_files(self):
        lib.list_files(self)

    @run_as('manager')
    def list_dirs(self):
        lib.list_dirs(self)

    @run_as('root')
    def install(self):
        lib.install(self)

    @run_as('root')
    def upgrade(self):
        lib.upgrade(self)

    @run_as('manager')
    def ls(self):
        for item in queries.ls(self):
            print(item)

    @run_as('root')
    def uninstall(self):
        lib.uninstall(self)

    @run_as('manager')
    def db_list_files(self):
        for item in queries.db_list_files(self, self.args.param[0]):
            print(item)

    @run_as('manager')
    def db_list_generated(self):
        for item in queries.db_list_generated(self, self.args.param[0]):
            print(item)

    @run_as('manager')
    def db_list_dirs(self):
        for item in queries.db_list_dirs(self, self.args.param[0]):
            print(item)

    @run_as('manager')
    def check_system_integrity(self):
        integrity.check_system_integrity(self)

    @run_as('manager')
    def links(self):
        lib.links(self)

    @run_as('manager')
    def linked_by(self):
        lib.linked_by(self)

    @run_as('manager')
    def links_both(self):
        lib.links_both(self)

    @run_as('manager')
    def check_buildorder(self):
        lib.check_buildorder(self)

    @run_as('root')
    def upgrade_rebuild(self):
        lib.upgrade_rebuild(self)

    @run_as('manager')
    def sort(self):
        lib.sort(self)

    @run_as('root')
    def rebuild_world(self):
        lib.rebuild_world(self)

    @run_as('manager')
    def list_old_tarballs(self):
        lib.list_old_tarballs(self)

    @run_as('manager')
    def pull(self):
        sources.pull(self)

    @run_as('manager')
    def tags(self):
        sources.tags(self, self.args.param[0])


def main():
    with addons.db.DB('packagemanager') as db:
        PackageManager(db).main()


if __name__ == '__main__':
    main()
