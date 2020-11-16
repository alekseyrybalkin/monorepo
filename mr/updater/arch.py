import os

import mr.config


def get_arch_version(pkgname):
    arch_version = None

    pm_config = mr.config.Config('packagemanager', private=False).read()
    arch_packages = '{}/external-repos/arch-packages'.format(pm_config['sources_path'])
    arch_community = '{}/external-repos/arch-community'.format(pm_config['sources_path'])
    aur = '{}/aur'.format(pm_config['sources_path'])

    for repo in [arch_packages, arch_community, aur]:
        if repo != aur:
            arch_pkgbuild = '{}/{}/trunk/PKGBUILD'.format(repo, pkgname)
        else:
            arch_pkgbuild = '{}/aur-{}/PKGBUILD'.format(repo, pkgname)
        if os.path.exists(arch_pkgbuild):
            pkgver = None
            _pkgmajor = None
            _pkgminor = None
            _basever = None
            _patchlevel = None
            _commit = None
            with open(arch_pkgbuild, 'r') as inf:
                for line in inf:
                    if line.startswith('pkgver='):
                        pkgver = line.strip().replace('pkgver=', '')
                        break
            if pkgver:
                arch_vars = [
                    '_pkgmajor',
                    '_pkgminor',
                    '_basever',
                    '_patchlevel',
                    '_commit',
                    '_majorver',
                    '_minorver',
                    '_securityver',
                    '_updatever',
                ]
                with open(arch_pkgbuild, 'r') as inf:
                    for line in inf:
                        for var in arch_vars:
                            if line.startswith('{}='.format(var)):
                                value = line.strip().replace('{}='.format(var), '')
                                pkgver = pkgver.replace('${}'.format(var), value)
                                pkgver = pkgver.replace('${{{}}}'.format(var), value)

            pkgver = pkgver.replace('"', '')
            arch_version = pkgver

    return arch_version
