import argparse
import os
import shutil
import sys

import addons.db
import addons.shell
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
    'python-backcall': {'0.1.0'},
    'miniupnpc': {'2.1.20190408'},
    'runc': {'1.0.0rc10'},
    'libtool': {'2.4.6+42+gb88cebd5'},
    'gtk-doc': {'1.32+37+gefc3644'},
    'pango': {'1.44.7+11+g73b46b04'},
    'cairo': {'1.17.2+17+g52a7c79fd'},
    'fontconfig': {'2.13.91+24+g75eadca'},
    'linux-firmware': {'20200421.78c0348'},
    'gtk': {'3.24.17+22+g99bae0fb5f'},
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
    'libldap': 'openldap',
    'mypaint-brushes': 'mypaint-brushes1',
    'libxtrans': 'xtrans',
    'freetype': 'freetype2',
    'lcms': 'lcms2',
    'python-opengl': 'pyopengl',
}

relmon_ignores = {
    'python-backcall': {'0.1.0'},
    'fossil': {'2.11'},
    'inkscape': {'1.0beta', '1.0rc1'},
    'python': {'3.9.0'},
    'colm': {'0.14.1'},
    'mesa': {'20.1.0'},
}

repo_ignores = {
    'gnome-common': {'6.293'},
    'libxcomposite': {'0.6.1'},
    'colm': {'0.14.1'},
    'openssl': {'3.0.0.alpha1'},
}

series = {
    'linux': '5.4',
    'linux-api-headers': '5.4',
    'libsigc++': '2',
    'chromium': '81',
    'coffeescript': '1',
    'librsvg': '2.40',
    'mypaint-brushes': '1',
    'librevenge': '0.0',
    'libpipeline': '1',
    'python-sphinx': '2',
}

repo_postprocessing = {
    'nspr': '.rtm',
    'nss': '.rtm',
    'json-c': '.20200419',
    'mutt': '.rel',
    'libevent': '.stable',
    'openjdk': '.ga',
}

pkgbuild_fields = [
    'pkgname',
    'pkgver',
    'vcs',
    'vcs_pkgname',
    'relmon_id',
    'updater_rules',
]


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
    def __init__(self, db):
        self.relmon_checker = relmon.RelmonChecker(db)

    def update_pkgver(self, pkgbuild, old_pkgver, new_pkgver):
        with open(pkgbuild, 'r') as inf, open(pkgbuild + '.NEW', 'w') as outf:
            for line in inf.readlines():
                if line.strip() == 'pkgver={}'.format(old_pkgver):
                    outf.write('pkgver={}\n'.format(new_pkgver))
                else:
                    outf.write(line)
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

        relmon_version = None
        if pkg.relmon_id:
            relmon_version = self.relmon_checker.get_relmon_version(
                pkg.relmon_id,
                pkg.updater_rules,
                relmon_ignores.get(pkg.pkgname, []),
                series.get(pkg.pkgname),
            )

        repo_version = None

        dirname = pkg.pkgname if not pkg.vcs_pkgname else pkg.vcs_pkgname
        repo_version = repo.get_repo_version(
            pkg.pkgname,
            dirname,
            pkg.vcs,
            pkg.updater_rules,
            repo_ignores.get(pkg.pkgname, []),
            series.get(pkg.pkgname),
            self.verbose,
        )
        if repo_postprocessing.get(pkg.pkgname):
            repo_version = repo_version.replace(repo_postprocessing[pkg.pkgname], '')

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
        with open(pkgbuild, 'r') as f:
            for line in f.readlines():
                if line.strip() == 'pkgver={}'.format(pkg.pkgver):
                    can_change = True
                    break

        if arch_diff or relmon_diff or repo_diff or self.verbose or self.package:
            print('{:<30}{:<25}{:<25}{:<25}{}'.format(
                pkg.pkgname,
                pkg.pkgver,
                arch_version or 'N/A',
                relmon_version or 'N/A',
                repo_version or 'N/A',
            ))

            if self.in_place and can_change:
                diff_versions = []
                if arch_diff:
                    diff_versions.append((arch_parsed, arch_version))
                if relmon_diff:
                    diff_versions.append((relmon_parsed, relmon_version))
                if repo_diff:
                    diff_versions.append((repo_parsed, repo_version))

                if diff_versions:
                    best_version = sorted(diff_versions)[-1][1]
                    self.update_pkgver(pkgbuild, pkg.pkgver, best_version)

    def colorize(self, text, color=7):
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            seq = "\x1b[1;{}m".format(30 + color) + text + "\x1b[0m"
            return seq
        return text

    def check_all(self):
        sys.stdout.write(self.colorize('{:<30}{:<25}{:<25}{:<25}{}\n'.format(
            '[PACKAGE]',
            '[VERSION]',
            '[ARCH]',
            '[RELMON]',
            '[REPOSITORY]',
        ), color=8))
        for group in os.scandir('/home/rybalkin/projects/jinni-repo'):
            if group.is_dir():
                for project in os.scandir(group.path):
                    pkgbuild = os.path.join(project.path, 'PKGBUILD')
                    if project.is_dir() and os.path.exists(pkgbuild):
                        if not self.package or project.name == self.package:
                            self.process(pkgbuild)

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
    with addons.db.DB('relmon') as db:
        Updater(db).main()


if __name__ == '__main__':
    main()
