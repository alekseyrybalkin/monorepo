import json
import os

import addons.shell as shell


class Config:
    def __init__(self, name, private=True, defaults=None):
        self.name = name
        self.private = private
        self.defaults = defaults

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

        os.makedirs(os.path.dirname(conffile_path), exist_ok=True)

        if not os.path.exists(conffile_path):
            if defaults is None:
                raise ValueError('Config file does not exist and no defaults were provided')
            with open(conffile_path, 'tw') as conffile:
                if isinstance(defaults, str):
                    conffile.write(defaults)
                elif isinstance(defaults, dict):
                    conffile.write(json.dumps(defaults))
                else:
                    raise ValueError('Wrong default config format')

        with open(conffile_path, 'tr') as conffile:
            config = json.loads(conffile.read())
        return config
