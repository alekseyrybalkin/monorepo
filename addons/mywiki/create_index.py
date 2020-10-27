import sqlite3
import bz2
import os

from wikidb import DUMP_DATE, MYWIKI_HOME, DB, DUMP

INDEX = os.path.join(MYWIKI_HOME, 'enwiki-{}-pages-articles-multistream-index.txt'.format(DUMP_DATE))


_conn = sqlite3.connect(DB)
_cursor = _conn.cursor()

try:
    _cursor.execute('drop table wiki_index')
except sqlite3.OperationalError:
    pass

_cursor.execute('''
    create table wiki_index(
        name text primary key,
        start_byte integer,
        end_byte integer,
        idx integer
    )''')


def add_to_index(names, start_byte, end_byte):
    for i, name in enumerate(names):
        try:
            _cursor.execute(
                'insert into wiki_index(name, start_byte, end_byte, idx) values (?, ?, ?, ?)',
                (name, start_byte, end_byte, i),
            )
        except sqlite3.IntegrityError as e:
            print(e, name, start_byte, end_byte, i)
    _conn.commit()


chunks = 0

with open(INDEX, 'r') as index:
    start_byte = 0
    end_byte = 0
    names = []
    for line in index:
        new_start_byte, _, name = line.split(':', maxsplit=2)
        new_start_byte = int(new_start_byte)
        name = name.strip()

        if new_start_byte != start_byte:
            if start_byte == 0:
                start_byte = new_start_byte
            else:
                end_byte = new_start_byte - 1
                add_to_index(names, start_byte, end_byte)
                names = [name]
                start_byte = new_start_byte
                chunks += 1
                continue
        names.append(name)
    end_byte = os.stat(DUMP).st_size
    add_to_index(names, start_byte, end_byte)

_conn.close()
