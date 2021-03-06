import argparse
import datetime
import os
import signal
import subprocess
import sys
import time

import mr.config
import mr.db
import mr.shell as shell
import mr.updater.repo as repo


class SrcfetcherDatabase(mr.db.Database, metaclass=mr.db.DatabaseMeta):
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
        self.config = mr.config.Config('srcfetcher').read()

    def find_project(self, name):
        return self.db.select_one(
            'select id, name, path from project where name = ?',
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

    def get_oldest_expired(self, count=1):
        prev_date = datetime.datetime.now() - datetime.timedelta(days=2)
        return self.db.select_many(
            '''
                select name from project
                    where last_attempt is null or last_attempt <= ?
                    order by last_attempt asc
                    limit ?
            ''',
            (prev_date, count),
        )

    def get_all_failed(self):
        return self.db.select_many('select name from project where last_success <> last_attempt')

    def get_oldest_attempt_date(self):
        return self.db.select_one('select min(last_attempt) as time from project')

    def list_projects(self):
        sources_dir = os.path.join(shell.home(), '.data', 'sources')
        for group in (g for g in os.scandir(sources_dir) if g.is_dir() and g.name != '_ignore'):
            yield from ((project.name, project.path) for project in os.scandir(group) if project.is_dir())

    def pull_dir(self, project_name):
        if project_name in self.config['ignore']:
            return False

        project = self.find_project(project_name)
        if not project:
            raise ValueError('Project {} not found'.format(project_name))
        os.chdir(project['path'])

        try:
            for rule in self.config['pre_processing']:
                if rule['project'] == project_name:
                    shell.run(rule['command'])

            vcs = repo.guess_vcs(os.getcwd())
            if vcs == 'git':
                remotes = shell.output('git remote').split()
                for remote in remotes:
                    shell.run('git fetch -p --tags {}'.format(remote))

                if shell.output('git config --bool core.bare') == 'false':
                    shell.run('git merge --ff-only')
            elif vcs == 'mercurial':
                shell.run('hg pull')
            elif vcs == 'fossil':
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
        os.chdir(project['path'])

        try:
            vcs = repo.guess_vcs(os.getcwd())
            if vcs == 'git':
                remotes = shell.output('git remote').split()
                result = []
                for remote in remotes:
                    result.append((
                        'git',
                        shell.output('git remote get-url {}'.format(remote)),
                        remote,
                    ))
                return result
            elif vcs == 'mercurial':
                url = ''
                with open('.hg/hgrc', 'tr') as hgrc:
                    for line in hgrc:
                        if line.startswith('default = '):
                            url = line.replace('default = ', '').strip()
                            break
                return [('mercurial', url, '')]
            elif vcs == 'fossil':
                return [('fossil', shell.output('fossil remote-url'), '')]
        except subprocess.CalledProcessError:
            pass

        return []

    def update_url_list_file(self):
        if not os.path.exists(self.config['url_list_file']) \
                or time.time() - os.stat(self.config['url_list_file']).st_mtime > 12 * 3600:
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

        if not hasattr(self, 'args') or not self.args.quiet:
            sys.stdout.write(
                shell.colorize(
                    '{}: {}\n'.format(
                        project_name,
                        'ok' if success else 'failed',
                    ),
                    color=(2 if success else 1),
                ),
            )

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('projects', type=str, nargs='*')
        parser.add_argument('--quiet', action='store_true')
        return parser.parse_args()

    def main(self):
        # don't die when stopped, try to finish your job first
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

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
            existing_project = self.find_project(project)
            if existing_project is None:
                self.insert_project(project, path)
            elif existing_project['path'] != path:
                self.db.execute('update project set path=? where id=?', (path, existing_project['id']))
            db_projects.discard(project)

        for project in db_projects:
            self.delete_project(project)

        if self.args.projects:
            for project in self.args.projects:
                self.fetch(project)
        else:
            projects = self.get_oldest_expired(self.config['projects_per_run'])
            for project in projects:
                self.fetch(project['name'])
                time.sleep(2.0)


def main():
    with mr.db.DB('srcfetcher') as db:
        SourceFetcher(db).main()


if __name__ == '__main__':
    main()
