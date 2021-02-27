import sqlite3
import bz2
import os

import mr.config
import mr.db


class EncyclopediaDatabase(mr.db.Database, metaclass=mr.db.DatabaseMeta):
    def exists(self, cursor):
        cursor.execute('select 1 from wiki_index')

    def create(self, cursor):
        cursor.execute('''
            create table wiki_index(
                name text primary key,
                start_byte integer,
                end_byte integer,
                idx integer
            )''')

    def get_path(self):
        config = mr.config.Config('encyclopedia').read()
        return config['sqlite_index']


class SqliteIndexer:
    def __init__(self):
        self.config = mr.config.Config('encyclopedia').read()

    def add_to_index(self, db, names, start_byte, end_byte):
        for i, name in enumerate(names):
            try:
                db.execute(
                    'insert into wiki_index(name, start_byte, end_byte, idx) values (?, ?, ?, ?)',
                    (name, start_byte, end_byte, i),
                )
            except sqlite3.IntegrityError as e:
                print(e, name, start_byte, end_byte, i)

    def main(self):
        with mr.db.DB('encyclopedia') as db:
            db.execute('drop table wiki_index')

        with mr.db.DB('encyclopedia') as db:
            chunks = 0

            with bz2.open(self.config['article_index'], 'tr') as index:
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
                            self.add_to_index(db, names, start_byte, end_byte)
                            names = [name]
                            start_byte = new_start_byte
                            chunks += 1
                            continue
                    names.append(name)
                end_byte = os.stat(self.config['dump_file']).st_size
                self.add_to_index(db, names, start_byte, end_byte)


def main():
    SqliteIndexer().main()


if __name__ == '__main__':
    main()
