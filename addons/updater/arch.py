import os


def get_arch_version(pkgname):
    arch_version = None

    arch_packages = '/home/rybalkin/.data/sources/external-repos/arch-packages'
    arch_community = '/home/rybalkin/.data/sources/external-repos/arch-community'
    aur = '/home/rybalkin/.data/sources/aur'

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

            arch_version = pkgver

    return arch_version
