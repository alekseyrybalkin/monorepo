import glob
import os

import addons.ji.buildorder as buildorder
import addons.ji.common as common
import addons.ji.tarball as tarball
import addons.ji.upgrade as upgrade
import addons.shell as shell


def rebuild(pm, packages):
    for package in buildorder.sort(pm, packages):
        rebuild_world(pm, package, package)


def rebuild_world(pm, start_package=None, end_package=None):
    bom = buildorder.BuildOrderManager(pm)

    start_index = 0
    end_index = len(bom.order_index) - 1
    if start_package:
        start_index = bom.order_index[start_package]
    if end_package:
        end_index = bom.order_index[end_package]

    if end_index < start_index:
        raise ValueError('{} is before {} in buildorder'.format(end_package, start_package))

    for index in range(start_index, end_index + 1):
        package = bom.buildorder[index]
        if package == 'filesystem':
            continue
        print(f'rebuilding {package}')

        old_cwd = os.getcwd()
        repo_dir = common.get_repo_dir(pm, package)
        os.chdir(repo_dir)
        make.make(pm)

        glob_pattern = '*{}'.format(tarball.get_tarball_suffix())
        for tar in glob.iglob(glob_pattern):
            upgrade.upgrade(pm, tar)

        os.chdir(old_cwd)
