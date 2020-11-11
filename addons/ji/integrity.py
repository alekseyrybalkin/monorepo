import glob
import os

import addons.ji.queries as queries
import addons.ji.common as common
import addons.shell as shell


def list_untracked(pm, path):
    if not os.path.isdir(path):
        raise RuntimeError('dir {} does not exist'.format(path))

    for root, dirs, files in os.walk(path):
        for f in files:
            file_path = os.path.join(root, f)
            if not pm.db.select_one('select count(*) as cnt from file where name=?', (file_path,))['cnt']:
                print("nobody owns {}".format(file_path))


def list_missing(pm):
    for package in queries.ls(pm):
        for f in queries.db_list_files(pm, package):
            if not os.path.exists(f):
                print('{} is missing ({})'.format(f, package))
        for f in queries.db_list_generated(pm, package):
            if not os.path.exists(f):
                print('generated {} is missing ({})'.format(f, package))


def list_wrong_tarballs(pm):
    declared_tarballs = set()
    for root, dirs, files in os.walk(pm.config['repo_path']):
        for f in files:
            if f == 'PKGBUILD':
                pkgbuild = common.source_pkgbuild(pm, pkgbuild=os.path.join(root, 'PKGBUILD'))
                if pkgbuild['vcs']:
                    urls = pkgbuild['extra_urls'].split(' ')
                else:
                    urls = pkgbuild['urls'].split(' ') + pkgbuild['extra_urls'].split(' ')

                if pm.db.select_one('select id from package where name = ?', (pkgbuild['pkgname'],)):
                    for url in urls:
                        if url:
                            declared_tarballs.add(os.path.basename(url))

    actual_tarballs = set(os.listdir(pm.config['tarballs_path']))

    for tarball in declared_tarballs ^ actual_tarballs:
        print(tarball)


def check_system_integrity(pm):
    dirs = []
    for item in sorted(os.listdir('/')):
        full_dir = os.path.join('/', item)
        users = queries.who_uses_dir(pm, full_dir)
        if set(users) - set(['filesystem-1']):
            dirs.append(full_dir)

    print(' * searching for untracked files on filesystem...')
    print(' * used system dirs: {}'.format(' '.join(dirs)))
    for item in dirs:
        list_untracked(pm, item)

    print(' * searching for missing package files...')
    list_missing(pm)

    print(' * searching for duplications in package db...')
    for item in queries.list_duplicates(pm):
        print(item)

    print(' * searching for empty unknown folders...')
    for item in dirs:
        for root, dirs, files in os.walk(item):
            if not dirs and not files:
                if not queries.who_uses_dir(pm, root):
                    print(root)

    print(' * searching for wrong tarballs...')
    list_wrong_tarballs(pm)

    print(' * searching for unclean build dirs...')
    worker_name = pm.config['users']['worker']['name']
    for build_dir in  glob.iglob(os.path.join(shell.home(user=worker_name), 'build*')):
        print(build_dir)
