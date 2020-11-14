import glob
import os
import shutil
import stat
import subprocess
import time

import addons.packmgr.common as common
import addons.packmgr.tarball as tarball
import addons.shell as shell


def prepare(pm):
    pkgbuild = common.source_pkgbuild(pm)

    if pkgbuild['vcs']:
        urls = pkgbuild['extra_urls'].split(' ')
    else:
        urls = pkgbuild['urls'].split(' ') + pkgbuild['extra_urls'].split(' ')
    while '' in urls:
        urls.remove('')

    for url in urls:
        path = os.path.join(pm.config['tarballs_path'], os.path.basename(url))
        if not os.path.isfile(path):
            raise RuntimeError('file {} not found'.format(url))

    for item in os.listdir('.'):
        shell.run(
            'git ls-files {} --error-unmatch'.format(item),
            silent=True,
            user=pm.config['users']['manager']['uid'],
            group=pm.config['users']['manager']['gid'],
        )

    pkgbuild_path = os.path.join(os.getcwd(), 'PKGBUILD')
    shell.run(
        f'source {pkgbuild_path}; type prepare >/dev/null 2>&1 || function prepare() {{ :; }}; prepare',
        shell=True,
        user=pm.config['users']['manager']['uid'],
        group=pm.config['users']['manager']['gid'],
    )


def make(pm, package_name=None):
    if package_name:
        os.chdir(common.get_repo_dir(pm, package_name))
    old_cwd = os.getcwd()

    pm.prepare()
    tar_path = pm.make_worker()

    new_tar_path = os.path.join(old_cwd, os.path.basename(tar_path))
    shutil.move(tar_path, new_tar_path)
    shutil.chown(new_tar_path, pm.config['users']['manager']['uid'], pm.config['users']['manager']['gid'])
    shutil.rmtree(os.path.dirname(tar_path))


def make_worker(pm):
    os.environ['PATH'] = '{}:{}'.format('/usr/lib/ccache/bin', os.environ['PATH'])

    pkgbuild = common.source_pkgbuild(pm)

    builddir = os.path.join(
        shell.home(user=pm.config['users']['worker']['name']),
        'build.{}.{}'.format(pkgbuild['pkgname'], time.time()),
    )
    shutil.rmtree(builddir, ignore_errors=True)
    os.makedirs(builddir)
    for item in glob.iglob('*'):
        shutil.copy(item, builddir)

    os.chdir(builddir)
    pkgbuild = common.source_pkgbuild(pm)

    if pkgbuild['vcs']:
        vcs_repo = pkgbuild['pkgname']
        if pkgbuild['vcs_pkgname']:
            vcs_repo = pkgbuild['vcs_pkgname']
        vcs_repo_dir = common.find_vcs_repo_dir(pm, vcs_repo)

        if pkgbuild['vcs'] == 'git':
            shell.run('git clone -s -n {} {}'.format(vcs_repo_dir, pkgbuild['srcdir']))
            os.chdir(pkgbuild['srcdir'])
            if pkgbuild['gittag']:
                try:
                    shell.run('git fetch origin +refs/remotes/*:refs/remotes/origin/*')
                except subprocess.CalledProcessError:
                    pass
                shell.run('git checkout {}'.format(pkgbuild['gittag']))
            else:
                shell.run('git checkout origin/HEAD')
        if pkgbuild['vcs'] == 'mercurial':
            shell.run('hg clone {} {}'.format(vcs_repo_dir, pkgbuild['srcdir']))
            os.chdir(pkgbuild['srcdir'])
            if pkgbuild['hgtag']:
                shell.run('hg update -r {}'.format(pkgbuild['hgtag']))
        if pkgbuild['vcs'] == 'fossil':
            os.makedirs(pkgbuild['srcdir'])
            os.chdir(pkgbuild['srcdir'])
            shell.run('fossil open {}'.format(os.path.join(vcs_repo_dir, pkgbuild['pkgname'] + '.fossil')))
            if pkgbuild['fossiltag']:
                shell.run('fossil checkout {}'.format(pkgbuild['fossiltag']))
    else:
        if pkgbuild['srctar']:
            tar = os.path.join(pm.config['tarballs_path'], pkgbuild['srctar'])
            tarball.extract_all(tar, '.')
            os.chdir(pkgbuild['srcdir'])

    if not os.path.isdir(pkgbuild['srcdir']):
        os.makedirs(pkgbuild['srcdir'])
        os.chdir(pkgbuild['srcdir'])

    functions = ';'.join([
        (
            'function find_vcs_repo() {{      '
            '    find {}                      '
            '        -mindepth 2              '
            '        -maxdepth 2              '
            '        -type d                  '
            '        -name ${{1}}             '
            '    | grep -v _ignore;           '
            '}}                               '
        ).format(pm.config['sources_path']),
    ])
    env_vars = ';'.join([
        'location={}'.format(pkgbuild['location']),
        'srcdir={}'.format(pkgbuild['srcdir']),
        'tarballs_path={}'.format(pm.config['tarballs_path']),
    ])

    shell.run(
        '{}; {}; source ../PKGBUILD; set -e; build'.format(
            functions,
            env_vars,
        ),
        shell=True,
        user=pm.config['users']['worker']['uid'],
        group=pm.config['users']['worker']['gid'],
        tee=os.path.join(pkgbuild['location'], 'build.log'),
    )

    shell.run(
        'fakeroot {} make-fakeroot {}'.format(
            pm.config['exe'],
            pkgbuild['location'],
        ),
        user=pm.config['users']['worker']['uid'],
        group=pm.config['users']['worker']['gid'],
    )

    for dir_to_cleanup in pm.config['worker_cleanups']:
        shutil.rmtree(
            os.path.join(
                shell.home(user=pm.config['users']['worker']['name']),
                dir_to_cleanup,
            ),
            ignore_errors=True,
        )

    print(shell.colorize('make ok', color=2))

    tar = os.path.join(
        builddir,
        tarball.get_tarball_name(pkgbuild['pkgname'], pkgbuild['pkgver']),
    )
    return tar


def make_fakeroot(pm, location):
    os.chdir(location)
    pkgbuild = common.source_pkgbuild(pm)

    os.makedirs(pkgbuild['pkgdir'])
    os.chdir(pkgbuild['srcdir'])

    functions = ';'.join([
        (
            'function python_package() {      '
            '    pip install --no-deps        '
            '        --no-build-isolation     '
            '        --ignore-installed       '
            '        --compile                '
            '        --prefix=/usr            '
            '        --root=${pkgdir}         '
            '        .;                       '
            '}                                '
        ),
    ])
    env_vars = ';'.join([
        'pkgdir={}'.format(pkgbuild['pkgdir']),
        'location={}'.format(pkgbuild['location']),
        'srcdir={}'.format(pkgbuild['srcdir']),
    ])

    shell.run(
        '{}; {}; source ../PKGBUILD; set -e; package'.format(
            functions,
            env_vars,
        ),
        shell=True,
        user=pm.config['users']['worker']['uid'],
        group=pm.config['users']['worker']['gid'],
        tee=os.path.join(pkgbuild['location'], 'package.log'),
    )

    if os.path.exists(os.path.join(pkgbuild['pkgdir'], 'usr/share/info/dir')):
        os.remove(os.path.join(pkgbuild['pkgdir'], 'usr/share/info/dir'))

    if pkgbuild['pkgname'] != 'filesystem':
        for item in os.listdir(pkgbuild['pkgdir']):
            if item not in ['opt', 'boot', 'etc', 'usr']:
                raise RuntimeError('file/dir /{} is not allowed'.format(item))
        if os.path.exists(os.path.join(pkgbuild['pkgdir'], 'usr')):
            for item in os.listdir(os.path.join(pkgbuild['pkgdir'], 'usr')):
                if item not in ['bin', 'include', 'lib', 'share']:
                    raise RuntimeError('file/dir /usr/{} is not allowed'.format(item))
        for root, dirs, files in os.walk(pkgbuild['pkgdir']):
            for item in dirs + files:
                if ' ' in item:
                    raise RuntimeError('spaces in file/dir "{}" are not allowed'.format(item))

    if os.path.exists(os.path.join(pkgbuild['pkgdir'], 'usr/lib')):
        for root, dirs, files in os.walk(os.path.join(pkgbuild['pkgdir'], 'usr/lib')):
            for item in files:
                if item.endswith('.la'):
                    os.remove(os.path.join(root, item))

    if os.path.exists(os.path.join(pkgbuild['pkgdir'], 'usr/share/locale')):
        for item in os.listdir(os.path.join(pkgbuild['pkgdir'], 'usr/share/locale')):
            item_path = os.path.join(pkgbuild['pkgdir'], 'usr/share/locale', item)
            if os.path.isdir(item_path) and not item.startswith('en') and not item.startswith('ru'):
                shutil.rmtree(item_path)

    shutil.rmtree(os.path.join(pkgbuild['pkgdir'], 'usr/share/icons/hicolor'), ignore_errors=True)
    shutil.rmtree(os.path.join(pkgbuild['pkgdir'], 'usr/share/icons/locolor'), ignore_errors=True)

    if pkgbuild['generated_files']:
        for item in pkgbuild['generated_files'].split(' '):
            os.makedirs(os.path.join(pkgbuild['pkgdir'], os.path.dirname(item)), exist_ok=True)

    if not pkgbuild['disable_stripping']:
        if os.path.exists(os.path.join(pkgbuild['pkgdir'], 'usr/bin')):
            for root, dirs, files in os.walk(os.path.join(pkgbuild['pkgdir'], 'usr/bin')):
                for item in files:
                    try:
                        shell.run('strip --strip-debug {}'.format(os.path.join(root, item)), silent=True)
                    except subprocess.CalledProcessError:
                        pass
        if os.path.exists(os.path.join(pkgbuild['pkgdir'], 'usr/lib')):
            for root, dirs, files in os.walk(os.path.join(pkgbuild['pkgdir'], 'usr/lib')):
                for item in files:
                    try:
                        shell.run('strip --strip-debug {}'.format(os.path.join(root, item)), silent=True)
                    except subprocess.CalledProcessError:
                        pass

    os.makedirs(os.path.join(pkgbuild['pkgdir'], 'usr/share', pm.config['exe']), exist_ok=True)
    for item in ['PKGBUILD', 'build.log', 'package.log']:
        new_path = os.path.join(
            pkgbuild['pkgdir'],
            'usr/share',
            pm.config['exe'],
            '{}.{}'.format(pkgbuild['pkgname'], item),
        )
        shutil.move(
            os.path.join(pkgbuild['location'], item),
            new_path,
        )
        os.chmod(new_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

    with open(os.path.join(pkgbuild['pkgdir'], '.PKGINFO'), 'tw') as pkginfo:
        pkginfo.write('pkgname = {}\n'.format(pkgbuild['pkgname']))
        pkginfo.write('pkgbase = {}\n'.format(pkgbuild['pkgname']))
        pkginfo.write('pkgver = {}-1\n'.format(pkgbuild['pkgver']))
        pkginfo.write('pkgdesc = \n')
        pkginfo.write('url = \n')
        pkginfo.write('builddate = {}\n'.format(int(time.time())))
        pkginfo.write('packager = anonymous\n')
        pkginfo.write('arch = x86_64\n')

        if os.path.exists(os.path.join(pkgbuild['srcdir'], 'arch-depend')):
            with open(os.path.join(pkgbuild['srcdir'], 'arch-depend'), 'tr') as arch_depend:
                for line in arch_depend:
                    if line.startswith('provides = ') or line.startswith('depend = '):
                        pkginfo.write(line)

    tar = os.path.join(
        pkgbuild['location'],
        tarball.get_tarball_name(pkgbuild['pkgname'], pkgbuild['pkgver']),
    )
    tarball.create(pkgbuild['pkgdir'], tar)
