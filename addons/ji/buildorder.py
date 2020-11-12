import collections
import os

import addons.ji.common as common
import addons.ji.queries as queries
import addons.shell as shell


class BuildOrderManager:
    def __init__(self, pm):
        self.pm = pm
        self.buildorder = []

        buildorder_path = os.path.join(self.pm.config['repo_path'], 'buildorder')
        with open(buildorder_path, 'tr') as buildorder_file:
            for line in buildorder_file:
                line = line.strip()
                if line and not line.startswith('#'):
                    self.buildorder.append(line)

        self.order_index = {}
        for i, package in enumerate(self.buildorder):
            self.order_index[package] = i


def check_buildorder(pm):
    bom = BuildOrderManager(pm)

    pkgbuild_num = 0
    vcs_num = 0
    for root, dirs, files in os.walk(pm.config['repo_path']):
        for f in files:
            if f == 'PKGBUILD':
                pkgbuild_num += 1
                with open(os.path.join(root, 'PKGBUILD'), 'tr') as pkgbuild:
                    for line in pkgbuild:
                        if 'vcs=' in line:
                            vcs_num += 1
                            break

    db_num = len(queries.ls(pm))
    bo_num = len(bom.buildorder)
    print(' * db:          {}'.format(shell.colorize(str(db_num), color=7)))
    print(' * buildorder:  {}'.format(shell.colorize(str(bo_num), color=7 if bo_num == db_num else 1)))
    print(' * PKGBUILD:    {}'.format(shell.colorize(str(pkgbuild_num), color=7 if pkgbuild_num == db_num else 1)))
    print(' * vcs:         {}'.format(shell.colorize(str(vcs_num), color=7 if vcs_num == db_num else 1)))

    for package in queries.ls(pm):
        if package['name'] not in bom.order_index:
            print('{} is missing from buildorder'.format(package['name']))

    for package in bom.order_index:
        db_package = common.find_package(pm, package)
        if not db_package:
            print('{} is not installed, but is in buildorder'.format(package))

    for package, cnt in collections.Counter(bom.buildorder).most_common():
        if cnt > 1:
            print('duplicated in buildorder: {}'.format(package))
        else:
            break

    for package in queries.ls(pm):
        for parent in queries.links(pm, package['name']):
            if bom.order_index[parent['name']] > bom.order_index[package['name']]:
                if [package['name'], parent['name']] not in pm.config['buildorder_exceptions']:
                    print(shell.colorize('wrong order: {} -> {}'.format(package['name'], parent['name']), color=1))
