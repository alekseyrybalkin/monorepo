import os
import tarfile
import urllib.request

import addons.ji.common as common


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


def extract_file(pm, tar, member, path):
    with tarfile.open(tar, 'r') as tar:
        tar.extract(member, path=path)
