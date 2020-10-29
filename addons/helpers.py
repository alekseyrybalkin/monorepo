import os

import addons.shell as shell


def guess_distro():
    if not os.path.isfile('/usr/bin/ji'):
        return 'arch'
    if not os.path.isfile('/usr/bin/pacman'):
        return 'jinni'
    if os.path.isfile('/usr/share/pacman/keyrings/archlinux.gpg'):
        return 'arch'
    return 'jinni'
