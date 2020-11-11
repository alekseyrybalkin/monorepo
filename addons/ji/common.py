import os


def parse_pkgbuild():
    if not os.path.isfile('PKGBUILD'):
        raise RuntimeError('PKGBUILD not found in current directory')
    return None
