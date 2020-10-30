import argparse
import json
import os
import random
import re
import socket
import subprocess
import time

import addons.config
import addons.shell as shell


class MPW:
    def __init__(self):
        self.args = self.parse_args()
        self.config = addons.config.Config('mpw').read()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('command', type=str, default='', nargs='?')
        parser.add_argument('volume', type=int, default=100, nargs='?')
        parser.add_argument('--sorted', action='store_true')
        parser.add_argument('--reversed', action='store_true')

        return parser.parse_args()

    def send_command(self, command):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.config['socket'])
        sock.sendall('{{ "command": {} }}\n'.format(command).encode())
        time.sleep(0.05)
        data = sock.recv(2**16).decode()
        sock.close()
        return data

    def start_daemon(self):
        subprocess.Popen(
            'nohup mpv --input-ipc-server={} --idle=yes --loop-playlist=inf >/dev/null 2>&1 &'.format(
                self.config['socket']
            ),
            shell=True,
        )
        time.sleep(0.05)

    def populate_playlist(self, query=''):
        with open(self.config['playlist'], 'tw') as playlist:
            all_tracks = []
            for root, dirs, files in os.walk(self.config['music_library']):
                for track in files:
                    full_track = os.path.join(root, track)
                    if re.search(query, full_track):
                        all_tracks.append(full_track)
            if self.args.sorted:
                all_tracks = sorted(all_tracks)
            elif self.args.reversed:
                all_tracks = sorted(all_tracks)[::-1]
            else:
                random.shuffle(all_tracks)
            for track in all_tracks:
                playlist.write('{}\n'.format(track))

    def main(self):
        command_map = {
            'pause': '["set_property", "pause", true]',
            'play': '["set_property", "pause", false]',
            'volume': '["set_property", "volume", {}]'.format(self.args.volume),
            'next': '["playlist-next"]',
            'prev': '["playlist-prev"]',
            'stop': '["stop"]',
            'quit': '["quit"]',
        }
        if self.args.command in command_map:
            try:
                self.send_command(command_map[self.args.command])
                if self.args.command == 'play':
                    self.send_command('["loadlist", "{}"]'.format(self.config['playlist']))
            except (ConnectionRefusedError, FileNotFoundError):
                pass
            return
        if self.args.command == 'ls':
            try:
                answer = json.loads(self.send_command('["get_property", "filename"]'))
            except (ConnectionRefusedError, FileNotFoundError):
                return
            current_track = None
            if 'data' in answer:
                current_track = answer['data']
            with open(self.config['playlist'], 'tr') as playlist:
                tracks = []
                current_index = 0
                for index, track in enumerate(playlist):
                    track = track.strip()
                    tracks.append(track)
                    if current_track and track.endswith(current_track):
                        current_index = index

                ls_context = self.config['ls_context']
                print(shell.colorize('Total tracks in a playlist: {}'.format(len(tracks))))
                if current_index > self.config['ls_context']:
                    print('  ...')
                for index, track in enumerate(tracks):
                    if current_track and index == current_index:
                        print(shell.colorize('{:>4} {}'.format(index + 1, track), color=2))
                    elif index >= current_index - ls_context and index <= current_index + ls_context:
                        print('{:>4} {}'.format(index + 1, track))
                if current_index < len(tracks) - self.config['ls_context'] - 1:
                    print('  ...')
            return

        try:
            self.send_command('["get_property", "volume"]')
        except (ConnectionRefusedError, FileNotFoundError):
            self.start_daemon()
        self.populate_playlist(self.args.command)
        self.send_command('["loadlist", "{}"]'.format(self.config['playlist']))


def main():
    MPW().main()


if __name__ == '__main__':
    main()
