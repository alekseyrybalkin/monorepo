import argparse
import datetime
import os
import re
import shutil
import sys

import addons.db
import addons.relmon
import addons.shell
import addons.srcfetcher as srcfetcher
import addons.updater.relmon as relmon
import addons.updater.arch as arch
import addons.updater.repo as repo

special_ones = {
    'chromium',
    'libreoffice',
    'glibc',
    'gcc',
    'binutils',
    'llvm',
    'lld',
}

arch_ignores = {
    'miniupnpc': {'2.1.20190408'},
    'runc': {'1.0.0rc90'},
    'libtool': {'2.4.6+42+gb88cebd5'},
    'gtk-doc': {'1.32+37+gefc3644'},
    'pango': {'1.44.7+11+g73b46b04'},
    'cairo': {'1.17.2+25+gaee96d175'},
    'fontconfig': {'2.13.91+48+gfcb0420'},
    'linux-firmware': {'20200519.8ba6fa6'},
    'shared-mime-info': {'2.0+1+g6bf9e4f'},
    'openjdk': {'14.0.1.u7'},
}

arch_skips = {
    'filesystem',
    'which',
}

arch_names = {
    'nginx': 'nginx-mainline',
    'python-gunicorn': 'gunicorn',
    'python-docutils': 'docutils',
    'python-youtube-dl': 'youtube-dl',
    'python-pybind11': 'pybind11',
    'python-ipython': 'ipython',
    'python-cython': 'cython',
    'python-alabaster': 'python-sphinx-alabaster-theme',
    'libreoffice': 'libreoffice-fresh',
    'device-mapper': 'lvm2',
    'procps': 'procps-ng',
    'mpc': 'libmpc',
    'libxml': 'libxml2',
    'glib': 'glib2',
    'iproute': 'iproute2',
    'tidy-html5': 'tidy',
    'perl-ack': 'ack',
    'ublock': 'firefox-ublock-origin',
    'imlib': 'imlib2',
    'gtk': 'gtk3',
    'gdk-pixbuf': 'gdk-pixbuf2',
    'mypaint-brushes': 'mypaint-brushes1',
    'libxtrans': 'xtrans',
    'freetype': 'freetype2',
    'lcms': 'lcms2',
    'python-opengl': 'pyopengl',
    'openjdk': 'java-openjdk',
}

relmon_ignores = {
    'fossil': {'2.12'},
    'python': {'3.8.4', '3.9.0'},
    'colm': {'0.14.1'},
}

repo_ignores = {
    'gnome-common': {'06.0293'},
    'libxcomposite': {'0.6.1'},
    'colm': {'0.14.1'},
    'openssl': {
        '3.0.0.alpha1',
        '3.0.0.alpha2',
        '3.0.0.alpha3',
        '3.0.0.alpha4',
    },
}

series = {
    'linux': '5.7',
    'linux-api-headers': '5.7',
    'libsigc++': '2',
    'chromium': '81',
    'coffeescript': '1',
    'librsvg': '2.40',
    'mypaint-brushes': '1',
    'libpipeline': '1',
    'python-sphinx': '2',
    'python-sphinx_rtd_theme': '0.4',
}

repo_postprocessing = {
    'nspr': '.rtm',
    'nss': '.rtm',
    'json-c': '.20200419',
    'mutt': '.rel',
    'libevent': '.stable',
    'openjdk': '.ga',
}

arch_postprocessing = {
    'linux': '.arch.',
}

pkgbuild_fields = [
    'pkgname',
    'pkgver',
    'vcs',
    'vcs_pkgname',
    'relmon_id',
    'updater_rules',
]

custom = [
    'addons',
    'python-addons',
    'configs',
    'filesystem',
    'which',
    'initramfs',
    'lfs-book',
    'blfs-book',
    'opengl-docs',
    'lightlang',
    'ji',
    'telenoti',
    'syncema',
    'ttf-fonts',
]

one_check_ok = [
    'cpp-docs',
    'python-mwparserfromhell',
    'python-onetimepass',
    'vimium',
    'potrace',
    'gn',
    'pd',
    'zoom',
]

extra_repos = {
    'openjdk': ['openjdk'],
    'gmp': ['gmp'],
}


class Package:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__dict__[k] = v

    @classmethod
    def from_pkgbuild(cls, path):
        command = 'source {}; '.format(path)
        for field in pkgbuild_fields:
            command += 'echo ${}; '.format(field)
        values = [v.strip() for v in addons.shell.output([command], shell=True, strip=False).split('\n')[:-1]]

        return cls(**{k: v for k, v in zip(pkgbuild_fields, values)})


class Updater:
    def __init__(self, relmon_db, srcfetcher_db):
        self.relmon_checker = relmon.RelmonChecker(relmon_db)
        self.source_fetcher = srcfetcher.SourceFetcher(srcfetcher_db)
        self.relmon = addons.relmon.Relmon(relmon_db)

        self.no_checks = []
        self.one_check = []

    def update_pkgver(self, pkgbuild, old_pkgver, new_pkgver):
        with open(pkgbuild, 'r') as input_file, open(pkgbuild + '.NEW', 'w') as output_file:
            for line in input_file:
                if line.strip() == 'pkgver={}'.format(old_pkgver):
                    output_file.write('pkgver={}\n'.format(new_pkgver))
                else:
                    output_file.write(line)
        shutil.move(pkgbuild + '.NEW', pkgbuild)

    def process(self, pkgbuild):
        pkg = Package.from_pkgbuild(pkgbuild)

        if not self.special and pkg.pkgname in special_ones and not self.package:
            return
        if self.special and pkg.pkgname not in special_ones and not self.package:
            return

        arch_version = None
        if pkg.pkgname not in arch_skips:
            arch_name = pkg.pkgname if not arch_names.get(pkg.pkgname) else arch_names.get(pkg.pkgname)
            arch_version = arch.get_arch_version(arch_name)

        if arch_version and any(char in arch_version for char in '${}'):
            arch_version = None

        if arch_version and arch_postprocessing.get(pkg.pkgname):
            arch_version = re.sub(arch_postprocessing[pkg.pkgname], '', arch_version)

        relmon_version = None
        if pkg.relmon_id:
            relmon_version = self.relmon_checker.get_relmon_version(
                pkg.relmon_id,
                pkg.updater_rules,
                relmon_ignores.get(pkg.pkgname, []),
                series.get(pkg.pkgname),
            )

        repo_version = None

        dirnames = [pkg.pkgname if not pkg.vcs_pkgname else pkg.vcs_pkgname]
        dirnames.extend(extra_repos.get(pkg.pkgname, []))
        for dirname in dirnames:
            version = repo.get_repo_version(
                pkg.pkgname,
                dirname,
                pkg.vcs,
                pkg.updater_rules,
                repo_ignores.get(pkg.pkgname, []),
                series.get(pkg.pkgname),
                self.verbose and self.package,
            )
            if repo_version is None or (version is not None and repo_version < version):
                repo_version = version
        repo_version_jinni = False
        if repo_version:
            repo_version_jinni = repo_version.jinni
            repo_version = repo_version.to_version()

        if repo_version and repo_postprocessing.get(pkg.pkgname):
            repo_version = re.sub(repo_postprocessing[pkg.pkgname], '', repo_version)

        ver_parsed = repo.Tag(pkg.pkgver)
        arch_parsed = repo.Tag(arch_version) if arch_version else None
        relmon_parsed = repo.Tag(relmon_version) if relmon_version else None
        repo_parsed = repo.Tag(repo_version) if repo_version else None

        arch_diff = arch_parsed \
            and ver_parsed < arch_parsed \
            and (not arch_ignores.get(pkg.pkgname) or arch_version not in arch_ignores.get(pkg.pkgname)) \
            and (not series.get(pkg.pkgname) or arch_parsed.check_series(repo.Tag(series.get(pkg.pkgname))))

        relmon_diff = relmon_parsed and ver_parsed < relmon_parsed

        repo_diff = repo_parsed and ver_parsed < repo_parsed

        can_change = False
        with open(pkgbuild, 'r') as pkgbuild_file:
            for line in pkgbuild_file:
                if line.strip() == 'pkgver={}'.format(pkg.pkgver):
                    can_change = True
                    break

        if arch_diff or relmon_diff or repo_diff or self.verbose or self.package:
            diff_versions = []
            if arch_diff:
                diff_versions.append((arch_parsed, arch_version))
            if relmon_diff:
                diff_versions.append((relmon_parsed, relmon_version))
            if repo_diff:
                diff_versions.append((repo_parsed, repo_version))

            best_version = pkg.pkgver
            if diff_versions:
                best_version = sorted(diff_versions)[-1][1]

            if best_version != pkg.pkgver and self.in_place and can_change:
                self.update_pkgver(pkgbuild, pkg.pkgver, best_version)

            versions_to_print = []
            vers = [pkg.pkgver, arch_version, relmon_version, repo_version]
            for index, version in enumerate(vers):
                formatted = version or 'N/A'
                if version == best_version:
                    spaces = ''
                    if index < len(vers) - 1:
                        spaces = ' ' * (25 - len(version))
                    formatted = self.colorize(version, color=2) + spaces
                versions_to_print.append(formatted)

            jinni_tag = self.colorize('  [jinni]' if repo_version_jinni else '', color=1)
            print('{:<30}{:<25}{:<25}{:<25}{}'.format(
                pkg.pkgname,
                *versions_to_print[:-1], '{}{}'.format(versions_to_print[-1], jinni_tag)
            ))

        parsed_list = [arch_parsed, relmon_parsed, (repo_parsed if not repo_version_jinni else None)]
        checks = sum(1 if parsed else 0 for parsed in parsed_list)

        if checks == 0 and pkg.pkgname not in custom:
            self.no_checks.append(pkg.pkgname)
        if checks == 1 and pkg.pkgname not in custom and pkg.pkgname not in one_check_ok:
            self.one_check.append(pkg.pkgname)

    def colorize(self, text, color=7):
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            seq = "\x1b[1;{}m".format(30 + color) + text + "\x1b[0m"
            return seq
        return text

    def list_all_projects(self):
        projects = []
        for group in os.scandir('/home/rybalkin/projects/jinni-repo'):
            if group.is_dir():
                for project in os.scandir(group.path):
                    projects.append(project)
        return sorted(projects, key=lambda p: p.name)

    def check_all(self):
        problems = False

        failed = self.source_fetcher.get_all_failed()
        if failed:
            sys.stdout.write('Projects failed to update: ')
            sys.stdout.write(self.colorize(
                '{}\n'.format(' '.join(project['name'] for project in failed)),
                color=1,
            ))
            problems = True

        failed = self.relmon.get_all_failed()
        if failed:
            sys.stdout.write('Relmon ID update failures: ')
            sys.stdout.write(self.colorize(
                '{}\n'.format(str(len(failed))),
                color=1,
            ))
            problems = True

        last_attempt = self.source_fetcher.get_oldest_attempt_date()['time']
        last_attempt = datetime.datetime.strptime(last_attempt, '%Y-%m-%d %H:%M:%S.%f')
        hours = (datetime.datetime.now() - last_attempt).total_seconds() / 3600
        if hours >= 50:
            sys.stdout.write('Oldest fetch attempt:      {} hours ago\n'.format(
                self.colorize('{:.1f}'.format(hours), color=1),
            ))
            problems = True

        if problems:
            sys.stdout.write('\n')

        sys.stdout.write(self.colorize('{:<30}{:<25}{:<25}{:<25}{}\n'.format(
            '[PACKAGE]',
            '[VERSION]',
            '[ARCH]',
            '[RELMON]',
            '[REPOSITORY]',
        ), color=8))
        for project in self.list_all_projects():
            pkgbuild = os.path.join(project.path, 'PKGBUILD')
            if project.is_dir() and os.path.exists(pkgbuild):
                if not self.package or project.name == self.package:
                    self.process(pkgbuild)

        if self.no_checks or self.one_check:
            sys.stdout.write('\n')
        if self.no_checks:
            sys.stdout.write('Projects with no checks: ')
            sys.stdout.write(self.colorize(
                '{}\n'.format(' '.join(project for project in self.no_checks)),
                color=1,
            ))
        if self.one_check:
            sys.stdout.write('Projects with only one check: ')
            sys.stdout.write(self.colorize(
                '{}\n'.format(' '.join(project for project in self.one_check)),
                color=6,
            ))

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', type=str, default=None, help='package')
        parser.add_argument('-i', action='store_true', help='update versions in-place')
        parser.add_argument('-v', action='store_true', help='be verbose')
        parser.add_argument('-s', action='store_true', help='only special packages')
        args = parser.parse_args()

        return args.p, args.i, args.v, args.s

    def main(self):
        self.package, self.in_place, self.verbose, self.special = self.parse_args()
        self.check_all()


def main():
    with addons.db.DB('relmon') as relmon_db, addons.db.DB('srcfetcher') as srcfetcher_db:
        Updater(relmon_db, srcfetcher_db).main()


if __name__ == '__main__':
    main()
