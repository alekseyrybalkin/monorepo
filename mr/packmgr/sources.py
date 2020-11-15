import functools
import os

import mr.db
import mr.packmgr.common as common
import mr.shell as shell
import mr.srcfetcher
import mr.updater.repo as repo


def pull(pm, query):
    package = common.find_package(pm, query)
    repo_dir = common.get_repo_dir(pm, package['name'])
    pkgbuild = common.source_pkgbuild(pm, pkgbuild=os.path.join(repo_dir, 'PKGBUILD'))
    vcs_repo = package['name']
    if pkgbuild['vcs_pkgname']:
        vcs_repo = pkgbuild['vcs_pkgname']

    with mr.db.DB('srcfetcher') as db:
        mr.srcfetcher.SourceFetcher(db).fetch(vcs_repo)


def tags(pm, query):
    package = common.find_package(pm, query)
    repo_dir = common.get_repo_dir(pm, package['name'])
    pkgbuild = common.source_pkgbuild(pm, pkgbuild=os.path.join(repo_dir, 'PKGBUILD'))

    vcs_repo = package['name']
    if pkgbuild['vcs_pkgname']:
        vcs_repo = pkgbuild['vcs_pkgname']

    vcs_repo_dir = common.find_vcs_repo_dir(pm, vcs_repo)

    vcs = repo.guess_vcs(vcs_repo_dir)
    tags = repo.get_raw_tags(vcs_repo_dir, vcs)

    sort_key = functools.partial(
        repo.Tag,
        pkgname=package['name'],
        dirname=vcs_repo,
    )
    for tag in sorted(tags, key=sort_key):
        print(tag)

    real_version = pm.db.select_one("select version from package where id=?", (package['id'],))
    print()
    print('{} (installed)'.format(shell.colorize(real_version['version'], color=2)))
