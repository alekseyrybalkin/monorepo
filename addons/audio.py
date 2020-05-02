import concurrent.futures
import os

import addons.shell as shell

source_dir = '/home/rybalkin/.data/music/'
dest_dir = '/home/rybalkin/sandbox/music/'


def compress_file(src, dest):
    print('compressing {}'.format(src))
    shell.run(['ffmpeg', '-i', src, dest])


def compress():
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        for dirpath, dirnames, filenames in os.walk(source_dir):
            for name in filenames:
                dest_file = os.path.join(dest_dir, dirpath.replace(source_dir, ''), name)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                executor.submit(
                    compress_file,
                    os.path.join(dirpath, name),
                    dest_file,
                )
