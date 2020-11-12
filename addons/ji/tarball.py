import tarfile

import addons.ji.common as common


def download(pm):
    pkgbuild = common.source_pkgbuild(pm)


def list_files(pm, tar):
    with tarfile.open(tar, 'r') as tar:
        for member in tar.getmembers():
            if member.type != tarfile.DIRTYPE and member.name != '.PKGINFO':
                yield member


def list_dirs(pm, tar):
    with tarfile.open(tar, 'r') as tar:
        for member in tar.getmembers():
            if member.type == tarfile.DIRTYPE:
                yield member


def extract_file(pm, tar, member, path):
    with tarfile.open(tar, 'r') as tar:
        tar.extract(member, path=path)
