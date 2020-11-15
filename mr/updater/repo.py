import itertools
import os
import re

import mr.shell as shell
import mr.updater.versions as versions


def alphanum_split(part):
    raw_subparts = []

    is_num = False
    is_alpha = False
    subpart = ''

    for letter in part:
        if letter.isnumeric():
            if not subpart or subpart.isnumeric():
                subpart += letter
            else:
                raw_subparts.append(subpart)
                subpart = letter
        else:
            if not subpart or not subpart.isnumeric():
                subpart += letter
            else:
                raw_subparts.append(subpart)
                subpart = letter

    raw_subparts.append(subpart)

    subparts = []
    for subpart in raw_subparts:
        if subpart.isnumeric():
            subparts.append(int(subpart))
        else:
            subparts.append(subpart)

    return subparts


class Tag:
    def __init__(self, tag, pkgname=None, dirname=None, is_handmade=None):
        tag = re.sub('^release-', '', tag)
        tag = re.sub('^release_', '', tag)
        tag = re.sub('^release\\.', '', tag)
        tag = re.sub('^release_v', '', tag)
        tag = re.sub('^releases/', '', tag)
        tag = re.sub('^rel-', '', tag)
        tag = re.sub('^rel_', '', tag)
        tag = re.sub('^version-', '', tag)
        tag = re.sub('^version_', '', tag)
        tag = re.sub('^ver-', '', tag)
        tag = re.sub('^ver_', '', tag)
        tag = re.sub('^tag-', '', tag)
        tag = re.sub('^v', '', tag)
        tag = re.sub('^v_', '', tag)

        if is_handmade is not None:
            self.handmade = is_handmade
        else:
            self.handmade = tag.startswith('handmade-')
        tag = re.sub('^handmade-', '', tag)

        if pkgname and '+' not in pkgname:
            pkgname_variants = [pkgname.replace(a, b) for a in ['~', '_', '-', '.'] for b in ['~', '_', '-', '.']]
            for pkgname_variant in pkgname_variants:
                tag = re.sub('^{}-'.format(pkgname_variant), '', tag)
                tag = re.sub('^{}'.format(pkgname_variant), '', tag)
        if dirname and '+' not in dirname:
            tag = re.sub('^{}-'.format(dirname), '', tag)
            tag = re.sub('^{}'.format(dirname), '', tag)

        self.tag = tag
        self.raw_parts = [t for t in tag.replace('_', '.').replace('-', '.').split('.') if t]
        self.parts = []
        for part in self.raw_parts:
            if part:
                subparts = alphanum_split(part)
                self.parts.append(subparts)

    def to_version(self):
        return '.'.join(self.raw_parts)

    def __repr__(self):
        return "'{}'".format(self.to_version())

    def __lt__(self, other):
        for px, py in itertools.zip_longest(self.parts, other.parts):
            if px is None:
                if py and ''.join(str(subpart) for subpart in py) == '0':
                    continue
                return True
            if py is None:
                if px and ''.join(str(subpart) for subpart in px) == '0':
                    continue
                return False
            for x, y in itertools.zip_longest(px, py):
                if x is None:
                    return True
                if y is None:
                    return False
                if type(x) == type(y):
                    if x < y:
                        return True
                    if x > y:
                        return False
                else:
                    if type(x) == int:
                        return False
                    if type(x) == str:
                        return True
        return False

    def __eq__(self, other):
        return self.parts == other.parts

    def check_series(self, series):
        for px, py in itertools.zip_longest(self.parts, series.parts):
            if px is None:
                return False
            if py is None:
                continue
            for x, y in itertools.zip_longest(px, py):
                if x is None:
                    return False
                if y is None:
                    continue
                if type(x) == type(y):
                    if x != y:
                        return False
                else:
                    return False
        return True


def get_repo_dir(dirname):
    for entry in os.scandir('/home/rybalkin/.data/sources'):
        if entry.name != '_ignore' and entry.is_dir():
            for subentry in os.scandir(entry.path):
                if subentry.is_dir() and subentry.name == dirname:
                    return subentry.path
    return None


def guess_vcs(repo_dir):
    old_cwd = os.getcwd()
    os.chdir(repo_dir)

    vcs = None
    git_dir = shell.output('git rev-parse --git-dir')
    if git_dir == '.' or git_dir == '.git':
        vcs = 'git'
    elif os.path.isdir('.hg'):
        vcs = 'mercurial'
    elif os.path.isfile('.fslckout'):
        vcs = 'fossil'

    os.chdir(old_cwd)
    return vcs


def get_raw_tags(repo_dir, vcs):
    old_cwd = os.getcwd()
    os.chdir(repo_dir)

    if vcs == 'git':
        command = ['git', 'tag']
    elif vcs == 'mercurial':
        command = ['hg', 'tags', '-q']
    elif vcs == 'fossil':
        command = ['fossil', 'tag', 'list']
    else:
        raise RuntimeError('unknown vcs {}'.format(vcs))
    raw_tags = shell.output(command).split('\n')

    os.chdir(old_cwd)
    return raw_tags


def get_repo_version(pkgname, dirname, vcs, rules, ignores, series, verbose):
    rules = rules.split(',')

    repo_version = None

    repo_dir = get_repo_dir(dirname)
    if not repo_dir:
        return None
    os.chdir(repo_dir)

    if not vcs:
        vcs = guess_vcs(repo_dir)
    if not vcs:
        return None

    raw_tags = get_raw_tags(repo_dir, vcs)

    tags = [
        Tag(
            v.strip().lower(),
            pkgname=pkgname,
            dirname=dirname,
        ) for v in raw_tags
    ]

    tags = [
        Tag(
            versions.apply_rules(tag.to_version(), rules),
            pkgname=pkgname,
            dirname=dirname,
            is_handmade=tag.handmade,
        ) for tag in tags if versions.check_rules(tag.to_version(), rules)
    ]

    tags = [tag for tag in tags if tag.to_version() not in ignores]

    if series:
        tags = [tag for tag in tags if tag.check_series(Tag(series))]

    if verbose:
        print(sorted(tags))

    return sorted(tags)[-1] if tags else None
