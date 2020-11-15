import os
import re
import shutil

import mr.shell as shell


def get_battery_charges():
    charges = []
    if shutil.which('acpi'):
        acpi_output = shell.output('acpi')
        for line in acpi_output.split('\n'):
            charges.append(int(re.match(r'^.* (\d+)%.*$', line).group(1)))
    return charges
