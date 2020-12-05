import logging
import os
import pathlib
import subprocess
import sys

import telethon
import telethon.events
import socks

import mr.config
import mr.shell as shell


def run():
    logging.basicConfig(level=logging.INFO)

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
    session_file = os.path.join(
        sessions_dir,
        '{}.session'.format(config['client']['session_name']),
    )
    if not pathlib.Path(session_file).is_file():
        logging.error('no session file, run `sudo -u telenoti_user python -m mr.telegram.telenoti_login` first')
        sys.exit(1)

    api_id = config['client']['api_id']
    api_hash = config['client']['api_hash']

    client = telethon.TelegramClient(session_file, api_id, api_hash, proxy=proxy)

    sender_blacklist = set(sender['id'] for sender in config['blacklist']['senders'].values() if sender['blacklisted'])
    chats_blacklist = set(chat['id'] for chat in config['blacklist']['chats'].values() if chat['blacklisted'])

    @client.on(telethon.events.NewMessage(incoming=True))
    async def handle_new_message(event):
        if event.sender_id in sender_blacklist or event.chat_id in chats_blacklist:
            logging.info('ignoring message from sender {} in chat {}'.format(event.sender_id, event.chat_id))
            return

        sender = await event.get_sender()
        message_from = config['message']['from']
        message_to = config['message']['to']
        message_header = 'Telegram message from {}'.format(sender.username)

        lines = [
            'From: {} ({} {})'.format(sender.username, sender.first_name, sender.last_name),
            'Message: {}'.format(event.raw_text),
        ]
        if config['message']['debug']:
            lines += [
                'Sender ID: {}'.format(event.sender_id),
                'Chat ID: {}'.format(event.chat_id),
            ]
        message_body = '\n'.join(lines)

        logging.info('sending message from sender {} in chat {}'.format(event.sender_id, event.chat_id))
        cmdline = ['mail', '-Ssendwait', '-s', message_header, '-r', message_from, message_to]
        shell.run_with_input(cmdline, input_bytes=message_body.encode())

    client.start()
    client.run_until_disconnected()


if __name__ == '__main__':
    run()
