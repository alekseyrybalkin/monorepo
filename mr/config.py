import json
import os

import mr.shell as shell


class Config:
    def __init__(self, name, private=True, defaults=None, user=None):
        self.name = name
        self.private = private
        self.defaults = defaults
        self.user = user

    def read(self):
        if not self.private:
            conffile_path = os.path.join(
                '/etc',
                '{}.json'.format(self.name),
            )
        else:
            conffile_path = os.path.join(
                shell.home(user=self.user),
                '.config',
                'private',
                '{}.json'.format(self.name),
            )

        os.makedirs(os.path.dirname(conffile_path), exist_ok=True)

        if not os.path.exists(conffile_path):
            if self.defaults is None:
                raise ValueError('Config file does not exist and no defaults were provided')
            with open(conffile_path, 'tw') as conffile:
                if isinstance(self.defaults, str):
                    conffile.write(self.defaults)
                elif isinstance(self.defaults, dict):
                    conffile.write(json.dumps(self.defaults))
                else:
                    raise ValueError('Wrong default config format')

        with open(conffile_path, 'tr') as conffile:
            config = json.loads(conffile.read())
        return config
