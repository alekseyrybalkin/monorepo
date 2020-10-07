import json
import os

import addons.shell as shell


class Config:
    def __init__(self, name, private=True):
        self.name = name
        self.private = private

    def read(self):
        if not self.private:
            conffile_path = os.path.join(
                shell.home(),
                '.config',
                '{}.json'.format(self.name),
            )
        else:
            conffile_path = os.path.join(
                shell.home(),
                '.config',
                'private',
                '{}.json'.format(self.name),
            )
        with open(conffile_path, 'tr') as conffile:
            config = json.loads(conffile.read())
        return config
