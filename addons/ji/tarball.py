import tarfile

import addons.ji.common as common


def download(pm):
    pkgbuild = common.source_pkgbuild(pm)


def list_files(pm, query):
    with tarfile.open(query, 'r') as tar:
        for member in tar.getmembers():
            if member.type != tarfile.DIRTYPE and member.name != '.PKGINFO':
                yield member.name


def list_dirs(pm, query):
    with tarfile.open(query, 'r') as tar:
        for member in tar.getmembers():
            if member.type == tarfile.DIRTYPE:
                yield member.name
