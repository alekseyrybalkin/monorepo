import os
import tempfile
import time

import mr.shell as shell


class ArchAddons:
    def main(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            with open('.PKGINFO', 'tw') as pkginfo:
                pkginfo.write('''
pkgname = addons
pkgbase = addons
pkgver = 1-1
pkgdesc = addons
url = https://addons.com
builddate = {}
packager = anonymous
arch = x86_64
        '''.format(int(time.time())).strip() + '\n')
                with open('/etc/arch-depend', 'tr') as arch_depend:
                    for line in arch_depend:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            pkginfo.write(line + '\n')

            shell.run('tar cfa addons-1-1-x86_64.pkg.tar.gz .PKGINFO')
            shell.run('sudo pacman -U --noconfirm ./addons-1-1-x86_64.pkg.tar.gz')
            os.chdir(old_cwd)


def main():
    ArchAddons().main()


if __name__ == '__main__':
    main()
