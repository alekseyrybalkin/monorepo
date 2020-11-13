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
        shell.run('git ls-files {} --error-unmatch'.format(item), silent=True)

    pkgbuild_path = os.path.join(os.getcwd(), 'PKGBUILD')
    shell.run(
        f'source {pkgbuild_path}; type prepare >/dev/null 2>&1 || function prepare() {{ :; }}; prepare',
        shell=True,
        silent=True,
    )


def make(pm):
    pm.prepare()
    tar_path = pm.make_worker()
    new_tar_path = os.path.join(os.getcwd(), os.path.basename(tar_path))
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

#    cd /home/${HOUSECARL}/${BUILDDIR}/
#    unset srcdir
#    location=`pwd`
#    . ./PKGBUILD
#    pkgdir=${location}/${EXE}-dest
#    if [ -z "${srcdir}" ]; then
#        srcdir=${location}/${pkgname}-${pkgver}
#    fi
#
#    if [ ! -z ${vcs} ]; then
#        vcs_repo=${pkgname}
#        if [ -n "${vcs_pkgname}" ]; then
#            vcs_repo=${vcs_pkgname}
#        fi
#        vcs_repo=`find_vcs_repo ${vcs_repo}`
#        if [ ${vcs} == "git" ]; then
#            git clone -s -n ${vcs_repo} ${srcdir}
#            cd ${srcdir}
#            if [ ! -z ${gittag} ]; then
#                set +e
#                git fetch origin +refs/remotes/*:refs/remotes/origin/*
#                set -e
#                git checkout ${gittag}
#            else
#                if git branch -a | grep origin/HEAD >/dev/null 2>&1; then
#                    git checkout origin/HEAD
#                fi
#            fi
#        fi
#        if [ ${vcs} = 'mercurial' ]; then
#            hg clone ${vcs_repo} ${srcdir}
#            cd ${srcdir}
#            if [ ! -z ${hgtag} ]; then
#                hg update -r ${hgtag}
#            fi
#        fi
#        if [ ${vcs} = 'fossil' ]; then
#            mkdir ${srcdir}
#            cd ${srcdir}
#            fossil open ${vcs_repo}/${pkgname}.fossil
#            if [ ! -z ${fossiltag} ]; then
#                fossil checkout ${fossiltag}
#            fi
#        fi
#    else
#        if [[ ${srctar} ]]; then
#            echo "unpacking ${srctar}..."
#            tar xf ${TARBALLS_HOME}/${srctar}
#            cd ${srcdir}
#        fi
#    fi
#    if [ ! -d ${srcdir} ]; then
#        mkdir -p ${srcdir}
#        cd ${scrdir}
#    fi
#
#    PKG_CONFIG=/usr/bin/pkg-config
#    export PKG_CONFIG_PATH="/usr/lib/pkgconfig"
#
#    build 2>&1 | tee ${location}/make.log
#    make_exit_status=${PIPESTATUS[0]}
#    if [ ${make_exit_status} -gt 0 ]; then
#        exit ${make_exit_status}
#    fi
#
#    maker=${location}/maker.sh
#    cat > ${maker} << "EOF"
##!/bin/sh
#
#pip-install() {
#    pip install \
#        --no-deps \
#        --no-build-isolation \
#        --ignore-installed \
#        --compile \
#        --prefix=/usr \
#        --root=${pkgdir} .
#}
#
#python-package() {
#    pip-install
#}
#
#set -e
#cd ${location}
#. ./PKGBUILD
#rm -rf ${pkgdir}
#mkdir -p ${pkgdir}
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
#for f in PKGBUILD make.log install.log; do
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
#EOF
#    location=${location} srcdir=${srcdir} pkgdir=${pkgdir} \
#        pkgname=${pkgname} pkgver=${pkgver} \
#        TARBALLS_HOME=${TARBALLS_HOME} \
#        generated_files=${generated_files} \
#        PACMAN=${PACMAN} \
#        NO_STRIPPING=${NO_STRIPPING} EXE=${EXE} \
#        fakeroot bash ${maker}
#    cd ${location}
#    green='\e[0;32m'
#    txtrst='\e[0m'
#    rm -rf ~/.{cache,cmake,java,npm,config/configstore,cargo,fontconfig,local}
#    printf "${green}make ok${txtrst}\n"
#    exit 0

    tar = os.path.join(
        builddir,
        tarball.get_tarball_name(pkgbuild['pkgname'], pkgbuild['pkgver']),
    )
    #FIXME
    with open(tar, 'tr') as f:
        f.write('hello')
    print(tar)
