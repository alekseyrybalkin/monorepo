import glob
import os
import shutil
import time

import addons.ji.common as common
import addons.ji.tarball as tarball
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

    pm.prepare()
    tar_path = pm.make_worker()
    #FIXME uncomment
    #new_tar_path = os.path.join(os.getcwd(), os.path.basename(tar_path))
    #shutil.move(tar_path, new_tar_path)
    #shutil.chown(new_tar_path, pm.config['users']['manager']['uid'], pm.config['users']['manager']['gid'])
    #shutil.rmtree(os.path.dirname(tar_path))


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
    ])

    os.chdir(location)
    pkgbuild = common.source_pkgbuild(pm)

    os.makedirs(pkgbuild['pkgdir'])
    os.chdir(pkgbuild['srcdir'])

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

    #cd ${srcdir}
    #package 2>&1 | tee ${location}/install.log
    #install_exit_status=${PIPESTATUS[0]}
    #if [ ${install_exit_status} -gt 0 ]; then
    #    exit ${install_exit_status}
    #fi
    #
    ## fix /usr/share/info/dir
    #rm -fv ${pkgdir}/usr/share/info/dir
    #if [ "${pkgname}" != "filesystem" ]; then
    #    pushd ${pkgdir}
    #    regexp="^$"
    #    for i in /opt /boot /etc /usr; do
    #        regexp="${regexp}|^${i}$"
    #    done
    #    baddirs=`find . -maxdepth 1 -type d | sed "s/^\.//g" | grep -v -E "${regexp}"` && true
    #    if [ -n "${baddirs}" ]; then
    #        echo " *** ERROR ***: package tries to use bad dirs:"
    #        echo "${baddirs}"
    #        exit 1
    #    fi
    #    if [ -d usr ]; then
    #        for i in /usr/bin /usr/include /usr/lib /usr/share; do
    #            regexp="${regexp}|^${i}$"
    #        done
    #        baddirs=`find ./usr -maxdepth 1 -type d | sed "s/^\.//g" | grep -v -E "${regexp}"` && true
    #        if [ -n "${baddirs}" ]; then
    #            echo " *** ERROR ***: package tries to use bad dirs:"
    #            echo "${baddirs}"
    #            exit 1
    #        fi
    #        for i in /usr/sbin /usr/lib64; do
    #            regexp="${regexp}|^${i}$"
    #        done
    #        baddirs=`find ./usr -maxdepth 1 | sed "s/^\.//g" | grep -v -E "${regexp}"` && true
    #        if [ -n "${baddirs}" ]; then
    #            echo " *** ERROR ***: package tries to use bad non-dirs in /usr:"
    #            echo "${baddirs}"
    #            exit 1
    #        fi
    #    fi
    #    files_with_spaces=`find . | grep -E "\ "` || true
    #    if [ -n "${files_with_spaces}" ]; then
    #        echo " *** ERROR ***: package has file names with spaces:"
    #        echo "${files_with_spaces}"
    #        exit 1
    #    fi
    #    popd
    #fi
    #
    ## remove *.la files
    #if [ -d ${pkgdir}/usr/lib ]; then
    #    find ${pkgdir}/usr/lib -name "*.la" | xargs rm -vf
    #fi
    #
    ## remove unused translations
    #if [ -d ${pkgdir}/usr/share/locale ]; then
    #    for locale_dir in $(find ${pkgdir}/usr/share/locale -mindepth 1 -maxdepth 1 -type d); do
    #        [[ ${locale_dir} =~ "locale/en" ]] && continue
    #        [[ ${locale_dir} =~ "locale/ru" ]] && continue
    #        rm -rf ${locale_dir}
    #    done
    #fi
    #
    ## remove hicolor and locolor icons
    #if [ -d ${pkgdir}/usr/share/icons/hicolor ]; then
    #    rm -rf ${pkgdir}/usr/share/icons/hicolor
    #fi
    #if [ -d ${pkgdir}/usr/share/icons/locolor ]; then
    #    rm -rf ${pkgdir}/usr/share/icons/locolor
    #fi
    #
    ## install dirs for generated files
    #if [ -n "${generated_files}" ]; then
    #    for i in ${generated_files}; do
    #        mkdir -p ${pkgdir}/`dirname ${i}`
    #    done
    #fi
    #
    #if [ -z "${NO_STRIPPING}" ]; then
    #    echo "Stripping..."
    #    if [ -d "${pkgdir}/usr/bin" ]; then
    #        find ${pkgdir}/usr/bin -type f -exec strip --strip-debug '{}' ';' >/dev/null 2>&1
    #    fi
    #    if [ -d "${pkgdir}/usr/lib" ]; then
    #        find ${pkgdir}/usr/lib -type f -exec strip --strip-debug '{}' ';' >/dev/null 2>&1
    #    fi
    #fi
    #
    #cd ${location}
    #mkdir -p ${EXE}-dest/usr/share/${EXE}
    #for f in PKGBUILD build.log package.log; do
    #    mv ${f} ${EXE}-dest/usr/share/${EXE}/${pkgname}.${f}
    #done
    #
    #echo creating gz archive...
    #cd ${EXE}-dest
    #
    #echo "pkgname = ${pkgname}" > .PKGINFO
    #echo "pkgbase = ${pkgname}" >> .PKGINFO
    #echo "pkgver = ${pkgver}-1" >> .PKGINFO
    #echo "pkgdesc = " >> .PKGINFO
    #echo "url = " >> .PKGINFO
    #echo "builddate = $(date +%s)" >> .PKGINFO
    #echo "packager = ${EXE}" >> .PKGINFO
    #echo "arch = x86_64" >> .PKGINFO
    #
    #if [ -f ${srcdir}/arch-depend ]; then
    #    cat ${srcdir}/arch-depend | grep '^provides = ' >> .PKGINFO || true
    #    cat ${srcdir}/arch-depend | grep '^depend = ' >> .PKGINFO || true
    #fi
    #
    #{ find . | sed 's/^\.\///g'; } | sort | uniq | \
    #    tar cfa ../${pkgname}-${pkgver}-1-x86_64.pkg.tar.gz --no-recursion -T -
