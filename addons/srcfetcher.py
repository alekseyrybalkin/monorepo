import argparse
import datetime
import os
import signal
import subprocess
import sys
import time

import addons.config
import addons.db
import addons.shell as shell


class SrcfetcherDatabase(addons.db.Database, metaclass=addons.db.DatabaseMeta):
    def exists(self, cursor):
        cursor.execute('select 1 from project')

    def create(self, cursor):
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


class SourceFetcher:
    def __init__(self, db):
        self.db = db
        self.config = addons.config.Config('srcfetcher').read()

    def find_project(self, name):
        return self.db.select_one(
            'select path from project where name = ?',
            (name,),
        )

    def insert_project(self, name, path):
        now = datetime.datetime.now()
        self.db.execute(
            '''
                insert into project(name, path, last_attempt, last_success)
                    values (?, ?, ?, ?)
            ''',
            (name, path, now, now),
        )

    def delete_project(self, name):
        self.db.execute('delete from project where name = ?', (name,))

    def get_oldest_expired(self):
        prev_date = datetime.datetime.now() - datetime.timedelta(days=2)
        return self.db.select_one(
            '''
                select name from project
                    where last_attempt is null or last_attempt <= ?
                    order by last_attempt asc
                    limit 1
            ''',
            (prev_date,),
        )

    def get_all_failed(self):
        return self.db.select_many('select name from project where last_success <> last_attempt')

    def get_oldest_attempt_date(self):
        return self.db.select_one('select min(last_attempt) as time from project')

    def list_projects(self):
        sources_dir = os.path.join(shell.home(), '.data', 'sources')
        for group in (g for g in os.scandir(sources_dir) if g.is_dir() and g.name != '_ignore'):
            yield from ((project.name, project.path) for project in os.scandir(group) if project.is_dir())

    def colorize(self, text, color=7):
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            seq = "\x1b[1;{}m".format(30 + color) + text + "\x1b[0m"
            return seq
        return text

    def pull_dir(self, project_name):
        project = self.find_project(project_name)
        if not project:
            raise ValueError('Project {} not found'.format(project_name))
        os.chdir(self.find_project(project_name)['path'])

        try:
            for rule in self.config['pre_processing']:
                if rule['project'] == project_name:
                    shell.run(rule['command'])

            git_dir = shell.run('git rev-parse --git-dir')

            if os.path.isdir('.git/svn'):
                shell.run('git svn fetch')

                branches = shell.run('git branch -a').split()
                if any('origin/trunk' in branch for branch in branches):
                    shell.run('git merge --ff-only origin/trunk')
                else:
                    shell.run('git merge --ff-only git-svn')
            elif git_dir == '.' or git_dir == '.git':
                remotes = shell.run('git remote').split()
                for remote in remotes:
                    shell.run('git fetch -p --tags {}'.format(remote))

                if shell.run('git config --bool core.bare') == 'false':
                    shell.run('git merge --ff-only')
            elif os.path.isdir('.hg'):
                shell.run('hg pull')
            elif os.path.isfile('.fslckout'):
                shell.run('fossil pull')
                shell.run('fossil update')
            else:
                return False

            for rule in self.config['post_processing']:
                if rule['project'] == project_name:
                    shell.run(rule['command'])
        except subprocess.CalledProcessError:
            return False

        return True

    def get_info(self, project_name):
        project = self.find_project(project_name)
        if not project:
            raise ValueError('Project {} not found'.format(project_name))
        os.chdir(self.find_project(project_name)['path'])

        try:
            git_dir = shell.run('git rev-parse --git-dir')

            if os.path.isdir('.git/svn'):
                return [('git-svn', shell.run('git config svn-remote.svn.url'), '')]
            elif git_dir == '.' or git_dir == '.git':
                remotes = shell.run('git remote').split()
                result = []
                for remote in remotes:
                    result.append((
                        'git',
                        shell.run('git remote get-url {}'.format(remote)),
                        remote,
                    ))
                return result
            elif os.path.isdir('.hg'):
                url = ''
                with open('.hg/hgrc', 'tr') as hgrc:
                    for line in hgrc:
                        if line.startswith('default = '):
                            url = line.replace('default = ', '').strip()
                            break
                return [('mercurial', url, '')]
            elif os.path.isfile('.fslckout'):
                return [('fossil', shell.run('fossil remote-url'), '')]
        except subprocess.CalledProcessError:
            pass

        return []

    def update_url_list_file(self):
        if not os.path.exists(self.config['url_list_file']) or time.time() - os.stat(self.config['url_list_file']).st_mtime > 12 * 3600:
            with open(self.config['url_list_file'], 'tw') as url_list_file:
                for project, path in self.list_projects():
                    for (vcs, url, remote) in self.get_info(project):
                        group_project = '{}/{}'.format(os.path.basename(os.path.dirname(path)), project)
                        url_list_file.write('{:<42}{:<12}{:<10}{}\n'.format(group_project, vcs, remote, url))

    def fetch(self, project_name):
        success = self.pull_dir(project_name)
        now = datetime.datetime.now()
        if success:
            self.db.execute(
                '''
                    update project set last_attempt = ?, last_success = ?
                        where name = ?
                ''',
                (now, now, project_name),
            )
        else:
            self.db.execute(
                '''
                    update project set last_attempt = ?
                        where name = ?
                ''',
                (now, project_name),
            )

        if not self.args.quiet:
            sys.stdout.write(
                self.colorize(
                    '{}: {}\n'.format(
                        project_name,
                        'ok' if success else 'failed',
                    ),
                    color=(2 if success else 1),
                ),
            )

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('project', type=str, default='', nargs='?')
        parser.add_argument('--quiet', action='store_true')
        return parser.parse_args()

    def main(self):
        # don't die when stopped, try to finish your job first
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        os.environ['FOSSIL_HOME'] = os.path.join(shell.home(), '.config')

        self.args = self.parse_args()

        project_names = list(name for name, _ in self.list_projects())
        if len(set(project_names)) != len(project_names):
            for name in set(project_names):
                project_names.remove(name)
            raise ValueError('Duplicate package names in sources directory: {}'.format(project_names))

        self.update_url_list_file()

        rows = self.db.select_many('select name from project')
        db_projects = set(row['name'] for row in rows)

        for project, path in self.list_projects():
            existing_path = self.find_project(project)
            if existing_path is None:
                self.insert_project(project, path)
            db_projects.discard(project)

        # FIXME does not handle projects moving from one folder to another (e.g. gaming/lc0 -> dev/lc0)
        for project in db_projects:
            self.delete_project(project)

        if self.args.project:
            self.fetch(self.args.project)
        else:
            for i in range(3):
                project = self.get_oldest_expired()
                if project:
                    self.fetch(project['name'])
                    time.sleep(2.0)


def main():
    with addons.db.DB('srcfetcher') as db:
        SourceFetcher(db).main()


if __name__ == '__main__':
    main()
