import glob
import os

import mr.packmgr.buildorder as buildorder
import mr.packmgr.common as common
import mr.packmgr.make as make
import mr.packmgr.tarball as tarball
import mr.packmgr.upgrade as upgrade
import mr.shell as shell


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

        repo_dir = common.get_repo_dir(pm, package)

        with shell.popd(repo_dir):
            make.make(pm)

            os.chdir(repo_dir)
            glob_pattern = '*{}'.format(tarball.get_tarball_suffix())
            for tar in glob.iglob(glob_pattern):
                upgrade.upgrade(pm, tar)
