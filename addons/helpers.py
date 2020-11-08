import os
import re
import shutil

import addons.shell as shell


def get_battery_charges():
    charges = []
    if shutil.which('acpi'):
        acpi_output = shell.run('acpi')
        for line in acpi_output.split('\n'):
            charges.append(int(re.match(r'^.* (\d+)%.*$', line).group(1)))
    return charges
