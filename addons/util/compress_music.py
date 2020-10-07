import argparse
import concurrent.futures
import os

import addons.shell as shell


def compress_file(src, dest):
    print('compressing {}'.format(src))
    shell.run(['ffmpeg', '-i', src, dest])


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-dir', required=True, type=str, help='source dir')
    parser.add_argument('--destination-dir', type=str, default='/home/rybalkin/sandbox/music', help='destination dir')
    args = parser.parse_args()

    return args.source_dir, args.destination_dir


def compress():
    source_dir, destination_dir = parse_args()

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        for dirpath, dirnames, filenames in os.walk(source_dir):
            for name in filenames:
                dest_file = os.path.join(destination_dir, os.path.basename(dirpath), name)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                executor.submit(
                    compress_file,
                    os.path.join(dirpath, name),
                    dest_file,
                )


if __name__ == '__main__':
    compress()
