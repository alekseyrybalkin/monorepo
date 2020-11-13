import os
import shutil
import stat
import tempfile

import addons.ji.common as common
import addons.ji.gendb as gendb
import addons.ji.queries as queries
import addons.ji.tarball as tarball
import addons.shell as shell


def upgrade(pm, tar):
    if queries.list_duplicates(pm):
        raise RuntimeError('where are duplicates in the system, aborting')

    package = tarball.parse_package(tar)
    if package['name'] == 'filesystem':
        raise RuntimeError('cannot explicitly upgrade filesystem')

    db_package = common.find_package(pm, package['name'])

    new_version = package['version']
    old_version = db_package['version']
    print('upgrading {} from {} to {}'.format(package['name'], old_version, new_version))

    for item in tarball.list_files(pm, tar):
        file_path = os.path.join('/', item.name)
        owners = queries.who_owns(pm, file_path)
        if len(owners) > 1:
            raise RuntimeError('{} is owned by more than one package: {}'.format(
                file_path,
                [owner['name'] for owner in owners],
            ))
        if owners and owners[0]['name'] != package['name']:
            raise RuntimeError('{} is already owned by {}'.format(file_path, owners[0]['name']))
        if not owners and os.path.exists(file_path):
            raise RuntimeError('{} already exists and is not owned'.format(file_path))

    for item in tarball.list_dirs(pm, tar):
        dir_path = os.path.join('/', item.name)
        if os.path.exists(dir_path) and not os.path.isdir(dir_path):
            raise RuntimeError('{} already exists and is not a dir'.format(dir_path))

    tarball.extract_dirs(tar, '/')
    with tempfile.TemporaryDirectory() as tmpdir:
        tarball.extract_all(tar, tmpdir)

        old_cwd = os.getcwd()
        os.chdir(tmpdir)

        for item in tarball.list_files(pm, tar):
            shutil.move(item.name, os.path.join('/', item.name + '.{}'.format(pm.config['exe'])))
            shutil.move(os.path.join('/', item.name + '.{}'.format(pm.config['exe'])), os.path.join('/', item.name))

        os.chdir(old_cwd)

    old_dirs = set(queries.db_list_dirs(pm, package['name']))
    new_dirs = set(os.path.join('/', item.name) for item in tarball.list_dirs(pm, tar))

    for old_dir in old_dirs - new_dirs:
        users = queries.who_uses_dir(pm, old_dir)
        if len(users) == 1 and users[0]['name'] == package['name']:
            if not os.path.islink(old_dir) and not os.listdir(old_dir):
                os.rmdir(old_dir)

    old_files = set(queries.db_list_files(pm, package['name']))
    new_files = set(os.path.join('/', item.name) for item in tarball.list_files(pm, tar))

    for old_file in old_files - new_files:
        if os.path.exists(old_file):
            os.remove(old_file)

    if any(item.name == 'usr/share/info' for item in tarball.list_dirs(pm, tar)):
        common.recreate_info_dir()

    with tempfile.TemporaryDirectory() as tmpdir:
        relative_path = os.path.join('usr/share', pm.config['exe'], '{}.PKGBUILD'.format(package['name']))
        tarball.extract_file(tar, relative_path, tmpdir)
        shell.run(
            'source {}; type after_upgrade >/dev/null 2>&1 || function after_upgrade() {{ :; }}; after_upgrade'.format(
                os.path.join(tmpdir, relative_path),
            ),
            shell=True,
        )

    installed_path = os.path.join(pm.config['data_path'], 'installed')
    installed_tar = os.path.join(installed_path, os.path.basename(tar))
    shutil.move(
        tar,
        installed_tar,
    )
    shutil.chown(installed_tar, 'root', 'root')
    os.chmod(installed_tar, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

    gendb.gen_db(pm)
    shell.run('ldconfig')

    print(shell.colorize('upgrade ok', color=2))
