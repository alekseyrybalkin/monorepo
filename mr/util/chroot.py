import os
import shutil
import stat
import subprocess
import sys

import mr.shell as shell
import mr.util.hostconf


class ChrootManager:
    '''
    example usages:
    sudo chroot-enter
    sudo chroot-enter sudo -u someuser bash --login
    sudo -b chroot-enter sudo -u someuser someprogram >/dev/null 2>&1
    '''
    def is_mounted(self, chroot_dir):
        with open('/proc/mounts', 'tr') as mounts:
            for mount in mounts:
                if '{}/dev'.format(chroot_dir) in mount:
                    return True
        return False

    def main(self):
        mounts = ['/dev', '/dev/pts', '/dev/shm', '/proc', '/sys', '/run']

        if shell.user() != 'root':
            raise RuntimeError('should be run as root')

        command = sys.argv[1:]
        if not command:
            command += ['/bin/bash', '--login']

        chroot_dir = '/.{}'.format(mr.util.hostconf.HostConf().get_option('chroot'))
        extra_mount = mr.util.hostconf.HostConf().get_option('chroot_extra_mount').split(' ')

        if not self.is_mounted(chroot_dir):
            for mount in extra_mount + mounts:
                shell.run('mount {}{}'.format(chroot_dir, mount))

        tmp_devnull = '{}/tmp/devnull'.format(chroot_dir)
        os.makedirs(tmp_devnull, exist_ok=True)
        os.chmod(
            tmp_devnull,
            stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO,
        )

        subprocess.run(['chroot', chroot_dir] + command)

        ps_result = shell.output('ps auxfww')
        if ps_result.count('/usr/bin/chroot-enter') <= 1:
            try:
                shell.run('killall gpg-agent scdaemon xclip', silent=True)
            except subprocess.CalledProcessError:
                pass
            for mount in mounts[::-1] + extra_mount:
                shell.run('umount {}{}'.format(chroot_dir, mount))

            for item in os.listdir('{}/tmp'.format(chroot_dir)):
                shutil.rmtree(item, ignore_errors=True)


def main():
    ChrootManager().main()


if __name__ == '__main__':
    main()
