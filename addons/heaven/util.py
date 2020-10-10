import json
import os
import tempfile

import addons.shell as shell


def remote_upload_json(name, obj):
    with tempfile.TemporaryDirectory() as tmpdir:
        local_file_name = os.path.join(tmpdir, '{}.json'.format(name))
        with open(local_file_name, 'tw') as local_file:
            local_file.write(json.dumps(obj, indent=4))

        heaven = os.environ['HEAVEN']
        shell.run([
            'scp',
            local_file_name,
            '{}:/run/aleksey/private/{}.json'.format(heaven, name),
        ])


def remote_run(command):
    heaven = os.environ['HEAVEN']

    if isinstance(command, str):
        shell.run('ssh {} {}'.format(heaven, command))
    else:
        shell.run(['ssh', heaven] + command)


def local_read_json(name):
    with open('/run/aleksey/private/{}.json'.format(name), 'tr') as json_file:
        result = json.loads(json_file.read())
    return result


def local_remove_json(name):
    os.remove('/run/aleksey/private/{}.json'.format(name))
