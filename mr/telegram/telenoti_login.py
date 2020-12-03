import logging
import os

import telethon
import telethon.sync
import socks

import mr.config
import mr.shell as shell


def main():
    logging.basicConfig(level=logging.ERROR)

    config = mr.config.Config('telenoti').read()

    proxy = None
    if config['proxy']['enabled']:
        proxy = (socks.SOCKS5, config['proxy']['host'], config['proxy']['port'])

    sessions_dir = os.path.join(
        shell.home(),
        '.data',
        'secrets',
        'telenoti',
    )
    os.makedirs(sessions_dir, exist_ok=True)
    session_file = os.path.join(
        sessions_dir,
        '{}.session'.format(config['client']['session_name']),
    )
    api_id = config['client']['api_id']
    api_hash = config['client']['api_hash']

    with telethon.TelegramClient(session_file, api_id, api_hash, proxy=proxy) as client:
        pass


if __name__ == '__main__':
    main()
