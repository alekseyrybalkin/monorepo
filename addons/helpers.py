import os
import re
import shutil

import addons.shell as shell


def get_host_distro():
    if not os.path.isfile('/etc/hostdistro'):
        return 'unknown'
    with open('/etc/hostdistro', 'tr') as hostdistro:
        return hostdistro.read().strip()


def get_battery_charges():
    charges = []
    if shutil.which('acpi'):
        acpi_output = shell.run('acpi')
        for line in acpi_output.split('\n'):
            charges.append(int(re.match(r'^.* (\d+)%.*$', line).group(1)))
    return charges
