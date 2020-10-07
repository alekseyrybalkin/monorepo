import os

import onetimepass

import addons.shell as shell


def genpass():
    key_file = os.path.join(
        shell.home(),
        '.data',
        'secrets',
        'github-2fa.key',
    )
    secret = open(key_file, 'r').read().strip()
    token = onetimepass.get_totp(secret, as_string=True)
    shell.copy_to_clipboard(token.decode("UTF-8"))
