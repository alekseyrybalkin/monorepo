import os

import whoosh.index
import whoosh.fields

import mr.db
import mr.encyclopedia.create_sqlite_index


class WhooshIndexer:
    def __init__(self, db):
        self.db = db
        self.config = mr.config.Config('encyclopedia').read()

    def main(self):
        if not os.path.exists(self.config['whoosh_index']):
            os.mkdir(self.config['whoosh_index'])

        schema = whoosh.fields.Schema(name=whoosh.fields.TEXT(stored=True))
        ix = whoosh.index.create_in(self.config['whoosh_index'], schema)

        cursor = self.db.conn.cursor()
        cursor.execute('select name from wiki_index')

        inc = 10000
        count = 0
        while True:
            count += inc
            print(count)
            rows = cursor.fetchmany(size=inc)

            writer = ix.writer()
            if not len(rows):
                break
            for row in rows:
                writer.add_document(name=row['name'])
            writer.commit()

        self.db.conn.commit()
        cursor.close()


def main():
    with mr.db.DB('encyclopedia') as db:
        WhooshIndexer(db).main()


if __name__ == '__main__':
    main()
