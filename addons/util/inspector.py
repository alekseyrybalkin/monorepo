import glob
import itertools
import os
import re
import shutil
import signal
import subprocess

import addons.config
import addons.db
import addons.helpers
import addons.shell as shell
import addons.valet


class Inspector:
    def __init__(self):
        self.config = addons.config.Config('inspector').read()

    def check_git_repo(self, repo):
        project = os.path.basename(repo)

        if not os.path.isdir(repo):
            return '{:<30} {}'.format(project, shell.colorize('not a directory', color=1))
        if not os.path.isdir(os.path.join(repo, '.git')):
            return '{:<30} {}'.format(project, shell.colorize('not a git repo', color=1))

        git_status = shell.output('git -C {} status'.format(repo))
        if 'On branch master' not in git_status:
            return '{:<30} {}'.format(project, shell.colorize('not on master branch', color=1))
        if 'nothing to commit, working tree clean' not in git_status:
            return '{:<30} {}'.format(project, shell.colorize('dirty', color=1))
        if 'Your branch is up to date' not in git_status:
            return '{:<30} {}'.format(project, shell.colorize('not up to date', color=3))
        return ''

    def check_rogue_processes(self):
        max_len = self.config['rogue_processes']['max_command_line_length']
        ps_result = shell.output('ps -axo args')
        for process in sorted(set(ps_result.split('\n'))):
            if process == 'COMMAND':
                continue
            if process.startswith('[') and process.endswith(']'):
                continue
            if process in self.config['rogue_processes']['whitelist']:
                continue
            if any(item in process for item in self.config['rogue_processes']['whitelist_substr']):
                continue

            print(process[:max_len], '' if len(process) <= max_len else '...')

    def check_amixer_settings(self):
        mixer_name_re = re.compile("^Simple mixer control '(.*)',(.*)$")
        channel_desc_re = re.compile(
            "  ([a-zA-Z ]+):([a-zA-Z0-9 ]+)(\\[([0-9]+)%\\])? *(\\[[-0-9\\.]+dB\\])? *(\\[(on|off)\\])?",
        )

        config_rules = self.config['amixer_rules']
        rules = {}
        for rule in config_rules:
            rules[tuple(rule['key'])] = tuple(rule['value'])

        amixer_output = shell.output('amixer scontents')

        current_channel = ''
        for line in amixer_output.split('\n'):
            if line.startswith('Simple mixer control'):
                match = mixer_name_re.match(line)
                current_mixer = '{} {}'.format(match.group(1), match.group(2))
            for channel in ['Mono', 'Front Left', 'Front Right']:
                if line.startswith('  {}: '.format(channel)):
                    match = channel_desc_re.search(line)
                    if match:
                        channel = match.group(1)
                        volume = match.group(4)
                        status = match.group(7)
                        v, s = rules.get((current_mixer, channel), (volume, status))
                        if v != volume or s != status:
                            print(current_mixer, channel, volume, status)

    def main(self):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

        if self.config['killall']:
            try:
                shell.run('killall -q {}'.format(' '.join(self.config['killall'])))
            except subprocess.CalledProcessError:
                pass

        for user in self.config['productive_users']:
            for project_dir in self.config['project_dirs']:
                project_dir = os.path.join(shell.home(user=user), project_dir)
                if os.path.isdir(project_dir):
                    for repo in glob.iglob(os.path.join(project_dir, '*')):
                        check_result = self.check_git_repo(repo)
                        if check_result:
                            print(check_result)
        for repo in self.config['special_projects']:
            check_result = self.check_git_repo(repo)
            if check_result:
                print(check_result)

        for consumer in self.config['consumer_users']:
            for consumer_dir in self.config['consumer_dirs']:
                consumer_dir = os.path.join(shell.home(user=consumer), consumer_dir)
                if os.path.isdir(consumer_dir):
                    for trash in itertools.chain(
                        glob.iglob(os.path.join(consumer_dir, '*')),
                        glob.iglob(os.path.join(consumer_dir, '.*')),
                    ):
                        print('{:<30} {}'.format(consumer, trash))

        self.check_rogue_processes()

        if shutil.which('amixer'):
            self.check_amixer_settings()

        charges = addons.helpers.get_battery_charges()
        for charge in charges:
            if charge < 91:
                print('battery is only {}% charged'.format(charge))

        if shutil.which('pacman'):
            if len(shell.output('pacman -Qm').split('\n')) != 1:
                print('pacman -Qm')
            try:
                if shell.output('pacman -Qdtt'):
                    print('pacman -Qdtt')
            except subprocess.CalledProcessError as e:
                if e.output:
                    print(e.output)
            try:
                if shell.output('pacman -Qett'):
                    print('pacman -Qett')
            except subprocess.CalledProcessError as e:
                if e.output:
                    print(e.output)

        with addons.db.DB('valet') as db:
            _, tasks, done, _ = addons.valet.Valet(db).get_data(toggle_done=False)
            undone_tasks = len([task for task in tasks if task not in done])
            if undone_tasks:
                print('undone tasks: {}'.format(undone_tasks))

        allowed_domains = self.config['allowed_domains']
        domains_config = addons.config.Config('domains').read()
        domain_count = len(list(itertools.chain(*domains_config['whitelist'].values())))
        if domain_count > allowed_domains:
            print('extra whitelisted domains: {}'.format(domain_count - allowed_domains))

        if shell.output('systemctl show --property=SystemState') != 'SystemState=running':
            shell.run('systemctl --failed')


def main():
    Inspector().main()


if __name__ == '__main__':
    main()
