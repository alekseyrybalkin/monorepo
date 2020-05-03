import os


def get_arch_version(pkgname):
    arch_version = None

    arch_packages = '/home/rybalkin/.data/sources/external-repos/arch-packages'
    arch_community = '/home/rybalkin/.data/sources/external-repos/arch-community'

    for repo in [arch_packages, arch_community]:
        arch_pkgbuild = '{}/{}/trunk/PKGBUILD'.format(repo, pkgname)
        if os.path.exists(arch_pkgbuild):
            pkgver = None
            _pkgmajor = None
            _pkgminor = None
            _basever = None
            _patchlevel = None
            _commit = None
            with open(arch_pkgbuild, 'r') as inf:
                for line in inf.readlines():
                    if line.startswith('pkgver='):
                        pkgver = line.strip().replace('pkgver=', '')
                    if line.startswith('_pkgmajor='):
                        _pkgmajor = line.strip().replace('_pkgmajor=', '')
                    if line.startswith('_pkgminor='):
                        _pkgminor = line.strip().replace('_pkgminor=', '')
                    if line.startswith('_basever='):
                        _basever = line.strip().replace('_basever=', '')
                    if line.startswith('_patchlevel='):
                        _patchlevel = line.strip().replace('_patchlevel=', '')
                    if line.startswith('_commit='):
                        _commit = line.strip().replace('_commit=', '')

            if pkgver:
                if _pkgmajor:
                    pkgver = pkgver.replace('$_pkgmajor', _pkgmajor)
                    pkgver = pkgver.replace('${_pkgmajor}', _pkgmajor)
                if _pkgminor:
                    pkgver = pkgver.replace('$_pkgminor', _pkgminor)
                    pkgver = pkgver.replace('${_pkgminor}', _pkgminor)
                if _basever:
                    pkgver = pkgver.replace('$_basever', _basever)
                    pkgver = pkgver.replace('${_basever}', _basever)
                if _patchlevel:
                    pkgver = pkgver.replace('$_patchlevel', _patchlevel)
                    pkgver = pkgver.replace('${_patchlevel}', _patchlevel)
                if _commit:
                    pkgver = pkgver.replace('$_commit', _commit)
                    pkgver = pkgver.replace('${_commit}', _commit)
            arch_version = pkgver

    return arch_version
