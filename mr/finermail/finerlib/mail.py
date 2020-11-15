import datetime
import email
import email.utils
import html
import html.parser
import re

UID_RE = re.compile(b'UID (\\d+)')
FOLDER_RE = re.compile(b'"/" (.+)')

BAD_DATE = datetime.datetime(9999, 12, 31)


class HTMLCleaner(html.parser.HTMLParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_tag = None
        self.current_attrs = None
        self.current_data = None
        self.result = ''

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.current_attrs = attrs

    def handle_data(self, data):
        self.current_data = data

    def handle_endtag(self, tag):
        if self.current_data and tag not in ['style', 'script']:
            self.result += ' ' + html.escape(self.current_data) + ' '

        self.current_tag = None
        self.current_attrs = None
        self.current_data = None


class Message:
    def __init__(self, uid, sender, subject, date, body=None, body_html=None):
        self.uid = uid
        self.sender = sender
        self.subject = subject
        self.date = date
        self.body = body
        self.body_html = body_html


def get_header(header, msg):
    if msg[header] is None:
        return None
    value = ''
    parts = email.header.decode_header(msg[header])
    try:
        for part in parts:
            if part[1] is not None:
                if 'unknown' not in part[1]:
                    value += part[0].decode(part[1])
                else:
                    value += str(part[0])
            else:
                if isinstance(part[0], bytes):
                    value += part[0].decode('ascii')
                else:
                    value += part[0]
    except Exception:
        value = '(header decode error)'
    return value


def get_folders(session):
    try:
        imap = session.imap

        status, folders = imap.list()
        if status != 'OK':
            return folders[0]
        folders = [FOLDER_RE.findall(f)[0].decode('ascii') for f in folders]

        return {
            'folders': folders,
        }
    except Exception as e:
        return str(e)


def get_message_headers(folder, session):
    try:
        imap = session.imap

        status, folders = imap.list()
        if status != 'OK':
            return folders[0]
        folders = [FOLDER_RE.findall(f)[0].decode('ascii') for f in folders]

        messages = []
        status, [size] = imap.select(mailbox=folder, readonly=True)
        if status != 'OK':
            return size
        try:
            size = int(size)

            if size > 0:
                status, data = imap.fetch(b'%d:%d' % (1, size), '(UID BODY[HEADER.FIELDS (SUBJECT DATE FROM)])')
                if status != 'OK':
                    return data[0]

                for m in data:
                    if not isinstance(m, bytes):
                        uid = UID_RE.findall(m[0])[0]
                        msg = email.message_from_bytes(m[1])
                        sender = get_header('from', msg)
                        subject = get_header('subject', msg)
                        date = BAD_DATE
                        if get_header('date', msg):
                            date_tz = email.utils.parsedate_tz(get_header('date', msg))
                            if date_tz is not None:
                                date = datetime.datetime.fromtimestamp(
                                    email.utils.mktime_tz(date_tz),
                                )
                        messages.append(Message(
                            uid=uid.decode('utf-8'),
                            sender=sender,
                            subject=subject,
                            date=date,
                        ))
        finally:
            imap.close()

        return {
            'folders': folders,
            'folder': folder,
            'size': size,
            'messages': messages,
        }
    except Exception as e:
        return str(e)


def get_message_details(uid, folder, session):
    try:
        imap = session.imap

        status, folders = imap.list()
        if status != 'OK':
            return folders[0]
        folders = [FOLDER_RE.findall(f)[0].decode('ascii') for f in folders]

        status, [size] = imap.select(mailbox=folder, readonly=True)
        if status != 'OK':
            return size

        try:
            size = int(size)

            status, data = imap.uid('FETCH', uid.encode('utf-8'), '(RFC822)')
            if status != 'OK':
                return data[0]
            if data[0] is None:
                return 'Message {} not found in folder {}'.format(uid, folder)

            msg = email.message_from_bytes(data[0][1])
            sender = get_header('from', msg)
            subject = get_header('subject', msg)
            date = BAD_DATE
            if get_header('date', msg):
                date = datetime.datetime.fromtimestamp(
                    email.utils.mktime_tz(email.utils.parsedate_tz(get_header('date', msg))),
                )
            body = ''
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(None, True)
                    enc = part.get_content_charset()
                    if enc:
                        body = body.decode(enc)
                    break

            body_html = ''
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    body_html = part.get_payload(None, True)
                    enc = part.get_content_charset()
                    if enc:
                        body_html = body_html.decode(enc)
                    break
            if body_html:
                cleaner = HTMLCleaner()
                cleaner.feed(body_html)
                body_html = cleaner.result

            m = Message(
                uid=uid.encode('utf-8'),
                sender=sender,
                subject=subject,
                date=date,
                body=body,
                body_html=body_html,
            )
        finally:
            imap.close()

        return {
            'folders': folders,
            'folder': folder,
            'size': size,
            'message': m,
        }
    except Exception as e:
        return str(e)


def delete_messages(uids, folder, session):
    try:
        imap = session.imap

        status, [size] = imap.select(mailbox=folder, readonly=False)
        if status != 'OK':
            return size

        try:
            status, data = imap.uid('STORE', ','.join(uids).encode('utf-8'), '+FLAGS', '\\Deleted')
            if status != 'OK':
                return data[0]

            status, data = imap.expunge()
            if status != 'OK':
                return data[0]
        finally:
            imap.close()
    except Exception as e:
        return str(e)


def move_messages(uids, from_folder, to_folder, session):
    try:
        imap = session.imap

        status, [size] = imap.select(mailbox=from_folder, readonly=False)
        if status != 'OK':
            return size

        try:
            status, data = imap.uid('COPY', ','.join(uids).encode('utf-8'), to_folder)
            if status != 'OK':
                return data[0]
        finally:
            imap.close()
    except Exception as e:
        return str(e)
    return delete_messages(uids, from_folder, session)


def create_folder(new_folder, session):
    try:
        imap = session.imap
        status, data = imap.create(new_folder)
        if status != 'OK':
            return data[0]
    except Exception as e:
        return str(e)


def delete_folder(folder, session):
    try:
        imap = session.imap

        status, [size] = imap.select(mailbox=folder, readonly=True)
        if status != 'OK':
            return size

        try:
            size = int(size)
            if size > 0:
                return 'Folder {} is not empty ({} messages)'.format(folder, size)

        finally:
            imap.close()
        status, data = imap.delete(folder)
        if status != 'OK':
            return data[0]
    except Exception as e:
        return str(e)
