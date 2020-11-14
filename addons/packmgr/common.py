import os

import addons.shell as shell


def source_pkgbuild(pm, pkgbuild=None):
    if pkgbuild is None:
        pkgbuild = os.path.join(os.getcwd(), 'PKGBUILD')

    if not os.path.isfile(pkgbuild):
        raise RuntimeError('PKGBUILD not found')

    pkgbuild_fields = [
        'pkgname',
        'pkgver',
        'vcs',
        'vcs_pkgname',
        'gittag',
        'hgtag',
        'fossiltag',
        'urls',
        'extra_urls',
        'srcdir',
        'srctar',
        'relmon_id',
        'updater_rules',
        'generated_files',
        'disable_stripping',
    ]

    result = {}
    result['location'] = os.getcwd()

    command = 'unset {}; '.format(' '.join(pkgbuild_fields))
    command += 'location={}; '.format(result['location'])
    command += 'source {}; '.format(pkgbuild)
    for field in pkgbuild_fields:
        command += 'echo ${}; '.format(field)
    values = [v.strip() for v in shell.output(command, shell=True, strip=False).split('\n')]

    for key, value in zip(pkgbuild_fields, values):
        result[key] = value

    result['pkgdir'] = os.path.join(result['location'], '{}-dest'.format(pm.config['exe']))

    if not result['srcdir']:
        result['srcdir'] = os.path.join(result['location'], '{}-{}'.format(result['pkgname'], result['pkgver']))

    return result


def find_package(pm, query, none_ok=False):
    sql = "select id, name, version, timestamp from package where name = ? or name || '-' || version = ?;"
    package = pm.db.select_one(sql, (query, query))
    if not package:
        if none_ok:
            return None
        raise RuntimeError('package {} is not installed'.format(query))
    return package


def get_repo_dir(pm, package_name):
    for root, dirs, files in os.walk(pm.config['repo_path']):
        if 'PKGBUILD' in files and os.path.basename(root) == package_name:
            return root


def find_vcs_repo_dir(pm, vcs_repo):
    for root, dirs, files in os.walk(pm.config['sources_path']):
        if os.path.dirname(root) == pm.config['sources_path'] and vcs_repo in dirs:
            return os.path.join(root, vcs_repo)
        if root != pm.config['sources_path'] and os.path.dirname(root) != pm.config['sources_path']:
            dirs.clear()


def recreate_info_dir():
    old_cwd = os.getcwd()
    os.chdir('/usr/share/info')

    os.remove('dir')
    for info_file in os.listdir('.'):
        shell.run('install-info {} dir'.format(info_file))

    os.chdir(old_cwd)
