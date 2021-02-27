'''
1. Download wikipedia dump/index and index article names into sqlite
    https://dumps.wikimedia.freemirror.org/enwiki/

    $ time { python -m mr.encyclopedia.create_sqlite_index; }

    real    74m58.834s
    user    4m52.777s
    sys     10m39.487s

    $ ls -al ~/.data/encyclopedia/*.bz2 ~/.data/encyclopedia/sqlite.index.db
       212809630 Feb 26 21:19 /home/rybalkin/.data/encyclopedia/enwiki-20190601-pages-articles-multistream-index.txt.bz2
     17142482823 Feb 26 21:22 /home/rybalkin/.data/encyclopedia/enwiki-20190601-pages-articles-multistream.xml.bz2
      1746817024 Feb 26 21:18 /home/rybalkin/.data/encyclopedia/sqlite.index.db

2. Create whoosh index from sqlite index
    $ time { python -m mr.encyclopedia.create_whoosh_index; }

    $ du -ms ~/.data/encyclopedia/whoosh.index/
    2606    /home/rybalkin/.data/encyclopedia/whoosh.index/
'''
import datetime
import os

import bottle

import mr.db
import mr.encyclopedia.wikidb as wikidb

app = bottle.Bottle()
app_root = os.path.abspath(os.path.dirname(__file__))
bottle.TEMPLATE_PATH = [os.path.join(app_root, 'views')]


@app.route('/static/<filename>')
def static_file(filename):
    return bottle.static_file(filename, root=os.path.join(app_root, 'static'))


@app.route('/')
def searchpage():
    query = bottle.request.query.query
    results = []
    if query:
        with mr.db.DB('encyclopedia') as db:
            results = wikidb.WikiDB(db).get_search_results(query)
    return bottle.template(
        'searchresults',
        results=results,
        query=query,
        name=query,
        short_description=None,
    )


@app.route('/article')
def article():
    query = bottle.request.query.query
    name = bottle.request.query.name
    with mr.db.DB('encyclopedia') as db:
        article, source, short_description = wikidb.WikiDB(db).get_article(name, query)
    if article:
        if article == 'redirect':
            return bottle.redirect('/article?name={}&query={}'.format(source, query))
        return bottle.template(
            'article',
            article=article,
            source=source,
            query=query,
            name=name,
            short_description=short_description,
        )
    else:
        with mr.db.DB('encyclopedia') as db:
            results = wikidb.WikiDB(db).get_search_results(name)
        return bottle.template(
            'searchresults',
            results=results,
            query=name,
            name=name,
            short_description=None,
        )


def main():
    app.run(host='127.0.0.1', port=8003)


if __name__ == '__main__':
    main()
