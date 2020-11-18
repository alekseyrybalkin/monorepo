import os
import shutil

import mr.packmgr.common as common
import mr.packmgr.gendb as gendb
import mr.packmgr.queries as queries
import mr.packmgr.tarball as tarball
import mr.shell as shell


def uninstall(pm, query):
    if queries.list_duplicates(pm):
        raise RuntimeError('where are duplicates in the system, aborting')

    package = common.find_package(pm, query)
    if package['name'] == 'filesystem':
        raise RuntimeError('cannot uninstall filesystem')

    dependants = queries.linked_by(pm, package['name'])
    if dependants:
        raise RuntimeError(
            'uninstalling {} breaks dependencies for {}'.format(
                package['name'],
                '. '.join(dep['name'] for dep in dependants),
            )
        )

    for item in queries.db_list_files(pm, package['name']):
        if os.path.lexists(item):
            os.remove(item)

    dirs = queries.db_list_dirs(pm, package['name'])
    for item in sorted(dirs, key=len)[::-1]:
        users = queries.who_uses_dir(pm, item)
        if len(users) == 1 and users[0]['name'] == package['name']:
            if not os.path.islink(item) and not os.listdir(item):
                os.rmdir(item)

    if '/usr/share/info' in dirs:
        common.recreate_info_dir()

    installed_path = os.path.join(pm.config['data_path'], 'installed')
    uninstalled_path = os.path.join(pm.config['data_path'], 'uninstalled')

    tar = tarball.get_tarball_name(package['name'], package['version'])

    if os.path.isfile(os.path.join(installed_path, tar)):
        shutil.move(
            os.path.join(installed_path, tar),
            os.path.join(uninstalled_path, tar),
        )

    gendb.gen_db(pm)
    shell.run('ldconfig')
    print(shell.colorize('uninstall ok', color=2))
