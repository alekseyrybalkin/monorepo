import os

import addons.shell as shell


def source_pkgbuild(pm):
    if not os.path.isfile('PKGBUILD'):
        raise RuntimeError('PKGBUILD not found in current directory')

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

    command = 'location={};'.format(result['location'])
    command += 'source {}; '.format(os.path.join(os.getcwd(), 'PKGBUILD'))
    for field in pkgbuild_fields:
        command += 'echo ${}; '.format(field)
    values = [v.strip() for v in shell.run(command, shell=True, strip=False).split('\n')]

    for key, value in zip(pkgbuild_fields, values):
        result[key] = value

    result['pkgdir'] = os.path.join(result['location'], '{}-dest'.format(pm.config['exe']))

    if not result['srcdir']:
        result['srcdir'] = os.path.join(result['location'], '{}-{}'.format(result['pkgname'], result['pkgver']))

    return result
