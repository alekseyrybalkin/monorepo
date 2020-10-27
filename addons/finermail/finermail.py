'''
Missing features:
    - message management (search, view/change flags, etc.)
    - creating messages, replying
    - attachments (and different message parts overall)
    - folder renaming
    - configuration (e.g. session timeout is hardcoded)
    - paging
    - message threads

Currently only IMAPS is supported.
'''
import imaplib
import os
import random
import string

import bottle

import addons.finermail.finerlib.mail as finerlib_mail
import addons.finermail.finerlib.session as finerlib_session


SERVER = 'rybalkin.org'
LOGIN = 'aleksey@rybalkin.org'
app = bottle.Bottle()
app_root = os.path.abspath(os.path.dirname(__file__))
bottle.TEMPLATE_PATH = [os.path.join(app_root, 'views')]


@app.route('/static/<filename>')
def static_file(filename):
    return bottle.static_file(filename, root=os.path.join(app_root, 'static'))


@app.post('/')
def login_post():
    old_key = bottle.request.cookies.get('finer_session', None)
    password = bottle.request.forms.get('password', None)
    try:
        imap = imaplib.IMAP4_SSL(SERVER)
        imap.login(LOGIN, password)
    except Exception as e:
        error = str(e)
        return bottle.template(
            'login',
            page='login',
            login_error=error,
            title='Login - ',
        )

    key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(64))
    bottle.response.set_cookie('finer_session', key, max_age=3600, secure=False)
    if old_key is not None:
        finerlib_session.remove_session(old_key)
    finerlib_session.add_session(key, finerlib_session.Session(SERVER, LOGIN, imap))
    return bottle.redirect('/folder')


@app.get('/')
def login_get():
    session = finerlib_session.get_session(
        bottle.request.cookies.get('finer_session', None),
        SERVER,
        LOGIN,
    )
    if session is not None:
        logout = bottle.request.query.get('logout', None)
        if logout is not None:
            finerlib_session.remove_session(bottle.request.cookies.get('finer_session', None))
        else:
            return bottle.redirect('/folder')

    return bottle.template(
        'login',
        page='login',
        login_error=None,
        title='Login - ',
    )


@app.post('/folder')
def folder_post():
    session = finerlib_session.get_session(
        bottle.request.cookies.get('finer_session', None),
        SERVER,
        LOGIN,
    )
    if session is None:
        return bottle.redirect('/')

    folder = bottle.request.query.get('f', 'INBOX')

    command = bottle.request.forms.get('change')
    if command == 'command_delete':
        res = finerlib_mail.delete_messages(
            [mid[1:] for mid in bottle.request.forms if mid.startswith('m')],
            folder,
            session
        )
    elif command == 'command_move':
        res = finerlib_mail.move_messages(
            [mid[1:] for mid in bottle.request.forms if mid.startswith('m')],
            folder,
            bottle.request.forms.get('target_folder'),
            session
        )
    else:
        res = 'unknown command {}'.format(command)
    if isinstance(res, str) or isinstance(res, bytes):
        return bottle.template('error', page='error', error=res, title='Error - ')
    return bottle.redirect('/folder?f=' + folder)


@app.get('/folder')
def folder_get():
    session = finerlib_session.get_session(
        bottle.request.cookies.get('finer_session', None),
        SERVER,
        LOGIN,
    )
    if session is None:
        return bottle.redirect('/')

    folder = bottle.request.query.get('f', 'INBOX')

    res = finerlib_mail.get_message_headers(folder, session)
    if isinstance(res, str) or isinstance(res, bytes):
        return bottle.template('error', page='error', error=res)

    return bottle.template(
        'folder',
        page='folder',
        folders=sorted(res['folders']),
        folder=folder,
        size=res['size'],
        messages=reversed(sorted(res['messages'], key=lambda x: x.date)),
        bad_date=finerlib_mail.BAD_DATE,
        check_all=bottle.request.query.get('check_all', None),
        title='{} - '.format(folder),
    )


@app.route('/message/<uid>')
def message(uid):
    session = finerlib_session.get_session(
        bottle.request.cookies.get('finer_session', None),
        SERVER,
        LOGIN,
    )
    if session is None:
        return bottle.redirect('/')

    folder = bottle.request.query.get('f', 'INBOX')

    res = finerlib_mail.get_message_details(uid, folder, session)
    if isinstance(res, str) or isinstance(res, bytes):
        return bottle.template('error', page='error', error=res)

    return bottle.template(
        'message',
        page='message',
        folders=sorted(res['folders']),
        folder=folder,
        message=res['message'],
        bad_date=finerlib_mail.BAD_DATE,
        title=res['message'].subject,
    )


@app.post('/folders')
def folders_post():
    session = finerlib_session.get_session(
        bottle.request.cookies.get('finer_session', None),
        SERVER,
        LOGIN,
    )
    if session is None:
        return bottle.redirect('/')

    if bottle.request.query.get('create', ''):
        res = finerlib_mail.create_folder(bottle.request.forms.get('new_folder', ''), session)
        if isinstance(res, str) or isinstance(res, bytes):
            return bottle.template('error', page='error', error=res)
    elif bottle.request.query.get('delete', ''):
        res = finerlib_mail.delete_folder(bottle.request.forms.get('folder_to_delete', ''), session)
        if isinstance(res, str) or isinstance(res, bytes):
            return bottle.template('error', page='error', error=res)
    return bottle.redirect('/folders')


@app.get('/folders')
def folders_get():
    session = finerlib_session.get_session(
        bottle.request.cookies.get('finer_session', None),
        SERVER,
        LOGIN,
    )
    if session is None:
        return bottle.redirect('/')

    res = finerlib_mail.get_folders(session)
    if isinstance(res, str) or isinstance(res, bytes):
        return bottle.template('error', page='error', error=res)

    return bottle.template(
        'management',
        page='management',
        folders=sorted(res['folders']),
        folder=None,
        title='Folders - ',
    )


def main():
    app.run(host='127.0.0.1', port=8002)


if __name__ == '__main__':
    main()
