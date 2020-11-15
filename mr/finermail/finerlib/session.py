import hashlib
import datetime
import threading
import imaplib

SESSION_TIMEOUT = 3600  # seconds
SESSION_CLEANUP_INTERVAL = 60  # seconds


class Session:
    sessions = {}

    def __init__(self, server, login, imap):
        self.server = server
        self.login = login
        self.imap = imap
        self.created = datetime.datetime.now()

    def __str__(self):
        return 'finerlib.session.Session({}, {}, {}), created {}'.format(
            self.server, self.login, self.imap, self.created
        )


def get_session(key, server, login):
    if key is None:
        return None
    session = Session.sessions.get(hashlib.sha512(key.encode('utf-8')).hexdigest(), None)
    if session is not None and session.server == server and session.login == login:
        return session
    return None


def add_session(key, session):
    key_hash = hashlib.sha512(key.encode('utf-8')).hexdigest()
    Session.sessions[key_hash] = session


def remove_session(key, already_hashed=False):
    key_hash = hashlib.sha512(key.encode('utf-8')).hexdigest() if not already_hashed else key
    session = Session.sessions.get(key_hash, None)
    if session is not None:
        try:
            session.imap.logout()
        except imaplib.IMAP4.error:
            pass
        del Session.sessions[key_hash]
