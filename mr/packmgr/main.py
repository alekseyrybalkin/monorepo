import argparse
import fcntl
import functools
import os

import mr.config
import mr.db
import mr.packmgr.buildorder as buildorder
import mr.packmgr.gendb as gendb
import mr.packmgr.install as install
import mr.packmgr.integrity as integrity
import mr.packmgr.make as make
import mr.packmgr.queries as queries
import mr.packmgr.rebuild as rebuild
import mr.packmgr.sources as sources
import mr.packmgr.tarball as tarball
import mr.packmgr.uninstall as uninstall
import mr.packmgr.upgrade as upgrade
import mr.shell as shell
import mr.util.hostconf

config = mr.config.Config('packagemanager', private=False).read()


class PackageManagerDatabase(mr.db.Database, metaclass=mr.db.DatabaseMeta):
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
                is_dir integer,
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
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            old_egid = os.getegid()
            old_euid = os.geteuid()
            old_home = os.environ['HOME']
            old_logname = os.environ['LOGNAME']
            old_user = os.environ['USER']

            os.setegid(config['users'][user]['gid'])
            os.seteuid(config['users'][user]['uid'])
            old_umask = os.umask(config['users'][user]['umask'])
            os.environ['HOME'] = shell.home(user=config['users'][user]['name'])
            os.environ['LOGNAME'] = config['users'][user]['name']
            os.environ['USER'] = config['users'][user]['name']

            result = func(*args, **kwargs)

            os.environ['USER'] = old_user
            os.environ['LOGNAME'] = old_logname
            os.environ['HOME'] = old_home
            os.umask(old_umask)
            os.seteuid(old_euid)
            os.setegid(old_egid)

            return result
        actions[func.__name__] = wrapper
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

    def lockfile(self):
        kernel = mr.util.hostconf.HostConf().get_option('kernel')
        return '{}.{}'.format(self.config['lockfile'], kernel)

    def acquire_lock(self):
        with open(self.lockfile(), 'w') as lockfile:
            fcntl.lockf(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def release_lock(self):
        with open(self.lockfile(), 'w') as lockfile:
            fcntl.lockf(lockfile, fcntl.LOCK_UN)

    def do_action(self):
        action_aliases = {
            'l': 'links-both',
            'u': 'rebuild',
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
        package_name = self.args.param[0] if len(self.args.param) > 0 else None
        make.make(self, package_name)

    @run_as('worker')
    def make_worker(self):
        return make.make_worker(self)

    @run_as('worker')
    def make_fakeroot(self):
        return make.make_fakeroot(self, self.args.param[0])

    @run_as('manager')
    def download(self):
        tarball.download(self)

    @run_as('root')
    def gen_db(self):
        self.acquire_lock()
        try:
            gendb.gen_db(self)
        finally:
            self.release_lock()

    @run_as('manager')
    def who_owns(self):
        for item in queries.who_owns(self, self.args.param[0]):
            print('{}-{}'.format(item['name'], item['version']))

    @run_as('manager')
    def who_uses_dir(self):
        for item in queries.who_uses_dir(self, self.args.param[0]):
            print('{}-{}'.format(item['name'], item['version']))

    @run_as('manager')
    def check_conflicts(self):
        for conflict in tarball.check_conflicts(self, self.args.param[0]):
            print(conflict)

    @run_as('manager')
    def list_files(self):
        for item in tarball.list_files(self, self.args.param[0]):
            print(os.path.join('/', item.name))

    @run_as('manager')
    def list_dirs(self):
        for item in tarball.list_dirs(self, self.args.param[0]):
            print(os.path.join('/', item.name))

    @run_as('root')
    def install(self):
        self.acquire_lock()
        try:
            install.install(self, self.args.param[0])
        finally:
            self.release_lock()

    @run_as('root')
    def upgrade(self):
        self.acquire_lock()
        try:
            upgrade.upgrade(self, self.args.param[0])
        finally:
            self.release_lock()

    @run_as('manager')
    def ls(self):
        for item in queries.ls(self):
            print('{}-{}'.format(item['name'], item['version']))

    @run_as('root')
    def uninstall(self):
        self.acquire_lock()
        try:
            uninstall.uninstall(self, self.args.param[0])
        finally:
            self.release_lock()

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
    def check(self):
        buildorder.check_buildorder(self)
        integrity.check_system_integrity(self)

    @run_as('manager')
    def links(self):
        for item in queries.links(self, self.args.param[0]):
            print(item['name'])

    @run_as('manager')
    def linked_by(self):
        for item in queries.linked_by(self, self.args.param[0]):
            print(item['name'])

    @run_as('manager')
    def links_both(self):
        for item in queries.links(self, self.args.param[0]):
            print(item['name'])
        print('---')
        for item in queries.linked_by(self, self.args.param[0]):
            print(item['name'])

    @run_as('root')
    def rebuild(self):
        self.acquire_lock()
        try:
            rebuild.rebuild(self, self.args.param)
        finally:
            self.release_lock()

    @run_as('root')
    def rebuild_world(self):
        self.acquire_lock()
        try:
            start_package = self.args.param[0] if len(self.args.param) > 0 else None
            end_package = self.args.param[1] if len(self.args.param) > 1 else None
            rebuild.rebuild_world(self, start_package, end_package)
        finally:
            self.release_lock()

    @run_as('manager')
    def sort(self):
        for item in buildorder.sort(self, self.args.param):
            print(item)

    @run_as('manager')
    def pull(self):
        sources.pull(self, self.args.param[0])

    @run_as('manager')
    def tags(self):
        sources.tags(self, self.args.param[0])


def main():
    with mr.db.DB('packagemanager') as db:
        PackageManager(db).main()


if __name__ == '__main__':
    main()
