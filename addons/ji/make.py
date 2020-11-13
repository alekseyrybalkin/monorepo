import os

import addons.ji.common as common
import addons.shell as shell


def prepare(pm):
    pkgbuild = common.source_pkgbuild(pm)

    if pkgbuild['vcs']:
        urls = pkgbuild['extra_urls'].split(' ')
    else:
        urls = pkgbuild['urls'].split(' ') + pkgbuild['extra_urls'].split(' ')
    urls.remove('')

    for url in urls:
        path = os.path.join(pm.config['tarballs_path'], os.path.basename(url))
        if not os.path.isfile(path):
            raise RuntimeError('file {} not found'.format(url))

    for item in os.listdir('.'):
        shell.run('git ls-files {} --error-unmatch'.format(item))

    pkgbuild_path = os.path.join(os.getcwd(), 'PKGBUILD')
    shell.run(
        f'source {pkgbuild_path}; type prepare >/dev/null 2>&1 || function prepare() {{ :; }}; prepare',
        shell=True,
    )


def make(pm):
    pkgbuild = common.source_pkgbuild(pm)
    print(pkgbuild)


def make_worker(pm):
    pass
