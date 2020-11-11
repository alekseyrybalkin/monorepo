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
    ]

    result = {}
    result['location'] = os.getcwd()

    command = 'unset {}; '.format(' '.join(pkgbuild_fields))
    command += 'location={}; '.format(result['location'])
    command += 'source {}; '.format(pkgbuild)
    for field in pkgbuild_fields:
        command += 'echo ${}; '.format(field)
    values = [v.strip() for v in shell.run(command, shell=True, strip=False).split('\n')]

    for key, value in zip(pkgbuild_fields, values):
        result[key] = value

    result['pkgdir'] = os.path.join(result['location'], '{}-dest'.format(pm.config['exe']))

    if not result['srcdir']:
        result['srcdir'] = os.path.join(result['location'], '{}-{}'.format(result['pkgname'], result['pkgver']))

    return result


def find_package(pm, query):
    sql = "select id, name, version from package where name = ? or name || '-' || version = ?;"
    package = pm.db.select_one(sql, (query, query))
    if not package:
        raise RuntimeError('package {} is not installed'.format(query))
    return package