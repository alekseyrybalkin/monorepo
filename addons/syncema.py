import argparse
import imaplib
import logging
import mailbox
import os
import re
import signal
import sqlite3
import time

import addons.config


class IMAPTool:
    def __init__(self, imap):
        self.imap = imap

    def _check_error(self, status, response):
        if status != 'OK':
            raise RuntimeError(response[0])

    def get_folders(self):
        status, response = self.imap.list()
        self._check_error(status, response)

        folders = [re.findall(b'"/" (.+)', f)[0].decode() for f in response]
        return folders

    def select(self, folder, readonly=True):
        status, response = self.imap.select(mailbox=folder.encode(), readonly=readonly)
        self._check_error(status, response)
        size = int(response[0])
        return size

    def get_all_uids(self, folder):
        size = self.select(folder)
        if not size:
            return []

        status, response = self.imap.fetch(b'%d:%d' % (1, size), '(UID)')
        self._check_error(status, response)

        return [re.findall(b'UID (\\d+)', message)[0].decode() for message in response]

    def fetch_message(self, uid, folder):
        logging.info('fetching new message with uid = {} in folder = {}...'.format(uid, folder))

        self.select(folder)

        # fetch message body
        status, response = self.imap.uid('FETCH', uid.encode(), '(RFC822)')
        self._check_error(status, response)
        if response[0] is None:
            raise RuntimeError('Message {} not found in folder {}'.format(uid, folder))

        return response[0][1]

    def mark_as_read(self, uid, folder):
        self.select(folder, readonly=False)

        # mark message as read
        status, response = self.imap.uid('STORE', uid.encode(), '+FLAGS', '\\Seen')
        self._check_error(status, response)

    def delete_message(self, uid, folder):
        logging.info('expunging removed message with uid = {} in folder = {}...'.format(uid, folder))

        self.select(folder, readonly=False)

        # mark message for deletion
        status, response = self.imap.uid('STORE', uid.encode(), '+FLAGS', '\\Deleted')
        self._check_error(status, response)

        # expunge
        status, response = self.imap.expunge()
        self._check_error(status, response)

    def append_message(self, message, folder):
        logging.info('appending new message to folder = {}...'.format(folder))
        status, response = self.imap.append(folder.encode(), '', imaplib.Time2Internaldate(time.time()), message)
        self._check_error(status, response)
        return re.findall(b'APPENDUID (\\d+) (\\d+)', response[0])[0][1].decode()


class DBTool:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, timeout=0.1)
        self.cursor = self.conn.cursor()

        try:
            self.cursor.execute('select 1 from message')
        except sqlite3.OperationalError:
            self.cursor.execute('''
                create table message(
                    id integer primary key,
                    uid integer,
                    folder text,
                    maildir_id text
                )''')
            self.cursor.execute('''
                create table lock(
                    locked integer primary key
                )''')
            self.cursor.execute('create unique index uid_folder_idx on message(uid, folder)')
            self.cursor.execute('create index maildir_id_idx on message(maildir_id)')

        self.lock()

    def close(self):
        self.unlock()
        self.conn.commit()
        self.conn.close()

    def lock(self):
        self.cursor.execute('insert into lock(locked) values (1)')

    def unlock(self):
        self.cursor.execute('delete from lock')

    def add(self, uid, folder, maildir_id):
        self.cursor.execute(
            'insert into message(uid, folder, maildir_id) values (?, ?, ?)',
            (int(uid), folder, maildir_id),
        )

    def remove(self, uid, folder):
        self.cursor.execute('delete from message where uid = ? and folder = ?', (uid, folder))

    def check_is_new(self, uid, folder):
        self.cursor.execute('select id from message where uid = ? and folder = ?', (int(uid), folder))
        res = self.cursor.fetchone()
        return res is None

    def check_is_new_local(self, maildir_id, folder):
        self.cursor.execute('select id from message where maildir_id = ? and folder = ?', (maildir_id, folder))
        res = self.cursor.fetchone()
        return res is None

    def get_folder_listing(self, folder):
        self.cursor.execute('select uid, maildir_id from message where folder = ?', (folder,))
        return self.cursor.fetchall()


class ManagedDBTool:
    def __init__(self, db_path):
        self.db_path = db_path

    def __enter__(self):
        self.db = DBTool(self.db_path)
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()


class MaildirTool:
    def __init__(self, path):
        for subdir in ('cur', 'new', 'tmp'):
            if not os.path.exists(os.path.join(path, subdir)):
                os.makedirs(os.path.join(path, subdir))
        self.root = mailbox.Maildir(path)
        self.maildir = self.root

    def select(self, folder):
        self.maildir = self.root
        if folder != 'INBOX':
            if folder not in self.maildir.list_folders():
                self.maildir = self.maildir.add_folder(folder)
            else:
                self.maildir = self.maildir.get_folder(folder)
        self.maildir._refresh()

    def add(self, raw_message):
        message = mailbox.MaildirMessage(raw_message)

        # get current table of contents
        self.maildir._refresh()
        toc_before = dict(self.maildir._toc)

        # add new message
        self.maildir.add(message)

        # get new table of contents
        self.maildir._refresh()
        toc_after = dict(self.maildir._toc)

        # find out new message id from TOC diff
        new_id = list(set(toc_after) - set(toc_before))
        if len(new_id) != 1:
            raise RuntimeError('More or less than 1 message added at a time')

        return new_id[0]

    def exists(self, maildir_id):
        return maildir_id in self.maildir._toc

    def get_toc(self):
        return self.maildir._toc.keys()

    def get_message(self, maildir_id):
        return self.maildir.get_bytes(maildir_id)


class Syncema:
    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--quiet', action='store_true', help='reduce verbosity')
        return parser.parse_args()

    def read_config(self):
        cfg = addons.config.Config('syncema').read()

        if 'imap' not in cfg:
            raise ValueError('Section imap is missing from config')
        for key in ['secure', 'server', 'login', 'password', 'mark-as-read', 'timeout']:
            if key not in cfg['imap']:
                raise ValueError('Key imap.{} is missing from config'.format(key))
        if not cfg['imap']['secure']:
            raise ValueError('Only IMAPS is currently supported')
        if not isinstance(cfg['imap']['mark-as-read'], bool):
            raise ValueError('imap.mark-as-read must be boolean (true/false)')
        if not isinstance(cfg['imap']['timeout'], int):
            raise ValueError('imap.timeout must be integer')
        if cfg['imap']['timeout'] < 0:
            raise ValueError('imap.timeout must be non-negative')

        if 'maildir' not in cfg:
            raise ValueError('Section maildir is missing from config')
        for key in ['path']:
            if key not in cfg['maildir']:
                raise ValueError('Key maildir.{} is missing from config'.format(key))

        return cfg

    def main(self):
        # don't die when stopped, try to finish your job first
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        args = self.parse_args()
        if not args.quiet:
            logging.basicConfig(level=logging.INFO)

        cfg = self.read_config()
        db_path = os.path.join(cfg['maildir']['path'], 'syncema.db')

        server = cfg['imap']['server']
        timeout = cfg['imap']['timeout']

        with ManagedDBTool(db_path) as db, imaplib.IMAP4_SSL(server, timeout=timeout) as imap_conn:
            # initialize imap tool
            imap_conn.login(cfg['imap']['login'], cfg['imap']['password'])
            imap = IMAPTool(imap_conn)

            # initialize maildir tool
            maildir = MaildirTool(cfg['maildir']['path'])

            # get folder list
            folders = imap.get_folders()

            for folder in sorted(folders):
                # select correct maildir
                maildir.select(folder)

                # first, fetch all new messages from imap server
                for uid in imap.get_all_uids(folder):
                    if db.check_is_new(uid, folder):
                        maildir_id = maildir.add(imap.fetch_message(uid, folder))
                        db.add(uid, folder, maildir_id)
                        if cfg['imap']['mark-as-read'] == 'True':
                            imap.mark_as_read(uid, folder)

                # second, remove all locally deleted messages from imap server
                for uid, maildir_id in db.get_folder_listing(folder):
                    if not maildir.exists(maildir_id):
                        imap.delete_message(str(uid), folder)
                        db.remove(uid, folder)

                # third, append new locally created messages to imap server and store their new uids
                for maildir_id in maildir.get_toc():
                    if db.check_is_new_local(maildir_id, folder):
                        uid = imap.append_message(maildir.get_message(maildir_id), folder)
                        db.add(uid, folder, maildir_id)


def main():
    Syncema().main()


if __name__ == '__main__':
    main()
