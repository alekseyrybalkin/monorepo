import os
import shutil
import stat
import tempfile

import addons.packmgr.common as common
import addons.packmgr.gendb as gendb
import addons.packmgr.queries as queries
import addons.packmgr.tarball as tarball
import addons.shell as shell


def install(pm, tar):
    if queries.list_duplicates(pm):
        raise RuntimeError('where are duplicates in the system, aborting')

    package = tarball.parse_package(tar)
    if package['name'] == 'filesystem':
        raise RuntimeError('cannot explicitly install filesystem')

    db_package = common.find_package(pm, package['name'], none_ok=True)
    if db_package:
        raise RuntimeError('package {} is already installed'.format(package['name']))

    if tarball.check_conflicts(pm, tar):
        raise RuntimeError('where are conflicts, aborting')

    tarball.extract_all(tar, '/')

    if any(item.name == 'usr/share/info' for item in tarball.list_dirs(pm, tar)):
        common.recreate_info_dir()

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

    with tempfile.TemporaryDirectory() as tmpdir:
        relative_path = os.path.join('usr/share', pm.config['exe'], '{}.PKGBUILD'.format(package['name']))
        tarball.extract_file(installed_tar, relative_path, tmpdir)
        shell.run(
            'source {}; type after_install >/dev/null 2>&1 || function after_install() {{ :; }}; after_install'.format(
                os.path.join(tmpdir, relative_path),
            ),
            shell=True,
        )
    print(shell.colorize('install ok', color=2))
