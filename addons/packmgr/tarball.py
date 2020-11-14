import os
import tarfile
import urllib.request

import addons.packmgr.common as common


def get_tarball_suffix():
    return '-1-x86_64.pkg.tar.gz'


def get_tarball_name(name, version):
    return '{}-{}{}'.format(name, version, get_tarball_suffix())


def parse_package(tar):
    name, version = os.path.basename(tar).replace(get_tarball_suffix(), '').rsplit('-', 1)
    return {
        'name': name,
        'version': version,
    }


def download(pm):
    pkgbuild = common.source_pkgbuild(pm)
    if pkgbuild['vcs']:
        urls = pkgbuild['extra_urls'].split(' ')
    else:
        urls = pkgbuild['urls'].split(' ') + pkgbuild['extra_urls'].split(' ')

    for url in urls:
        if url:
            path = os.path.join(pm.config['tarballs_path'], os.path.basename(url))
            if os.path.isfile(path):
                continue
            print(f'downloading {url}...')
            with urllib.request.urlopen(url) as req, open(path, 'bw') as tar:
                tar.write(req.read())


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


def extract_file(tar, member, path):
    with tarfile.open(tar, 'r') as tar:
        tar.extract(member, path=path)


def extract_dirs(tar, path):
    with tarfile.open(tar, 'r') as tar:
        members = tar.getmembers()
        allowed_members = [member for member in members if member.type == tarfile.DIRTYPE]
        tar.extractall(members=allowed_members, path=path)


def extract_all(tar, path):
    with tarfile.open(tar, 'r') as tar:
        members = tar.getmembers()
        allowed_members = [member for member in members if member.name != '.PKGINFO']
        tar.extractall(members=allowed_members, path=path)


def check_conflicts(pm, tar):
    conflicts = []
    for item in list_files(pm, tar):
        full_path = os.path.join('/', item.name)
        if os.path.exists(full_path):
            conflicts.append('{} already exists on filesystem'.format(full_path))
    for item in list_dirs(pm, tar):
        full_path = os.path.join('/', item.name)
        if os.path.exists(full_path) and not os.path.isdir(full_path):
            conflicts.append('{} already exists on filesystem and is not a dir'.format(full_path))

    return conflicts


def create(subject_dir, tar_path):
    with tarfile.open(tar_path, 'w:gz') as tar:
        os.chdir(subject_dir)
        for item in os.listdir('.'):
            tar.add(item)
