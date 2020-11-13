import os
import shutil
import time

import addons.ji.common as common
import addons.ji.tarball as tarball
import addons.shell as shell


def prepare(pm):
    pkgbuild = common.source_pkgbuild(pm)

    if pkgbuild['vcs']:
        urls = pkgbuild['extra_urls'].split(' ')
    else:
        urls = pkgbuild['urls'].split(' ') + pkgbuild['extra_urls'].split(' ')
    while '' in urls:
        urls.remove('')

    for url in urls:
        path = os.path.join(pm.config['tarballs_path'], os.path.basename(url))
        if not os.path.isfile(path):
            raise RuntimeError('file {} not found'.format(url))

    for item in os.listdir('.'):
        shell.run('git ls-files {} --error-unmatch'.format(item), silent=True)

    pkgbuild_path = os.path.join(os.getcwd(), 'PKGBUILD')
    shell.run(
        f'source {pkgbuild_path}; type prepare >/dev/null 2>&1 || function prepare() {{ :; }}; prepare',
        shell=True,
        silent=True,
    )


def make(pm):
    pm.prepare()
    tar_path = pm.make_worker()
    new_tar_path = os.path.join(os.getcwd(), os.path.basename(tar_path))
    shutil.move(tar_path, new_tar_path)
    shutil.chown(new_tar_path, pm.config['users']['manager']['uid'], pm.config['users']['manager']['gid'])
    shutil.rmtree(os.path.dirname(tar_path))


def make_worker(pm):
    os.environ['PATH'] = '{}:{}'.format('/usr/lib/ccache/bin', os.environ['PATH'])

    pkgbuild = common.source_pkgbuild(pm)

    builddir = os.path.join(
        shell.home(user=pm.config['users']['worker']['name']),
        'build.{}.{}'.format(pkgbuild['pkgname'], time.time()),
    )

    # lots of stuff here

    tar = os.path.join(
        builddir,
        tarball.get_tarball_name(pkgbuild['pkgname'], pkgbuild['pkgver']),
    )
    print(tar)
