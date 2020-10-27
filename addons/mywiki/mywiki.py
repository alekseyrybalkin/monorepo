'''
https://dumps.wikimedia.freemirror.org/enwiki/

$ time { python create_index.py; }

real    74m58.834s
user    4m52.777s
sys     10m39.487s

$ ls -al ~/.data/docs/mywiki/enwiki* ~/.data/databases/large/wiki.db
  1746817024 Jun 10 12:15 .../wiki.db
   903452687 Jun 10 10:43 .../enwiki-20190601-pages-articles-multistream-index.txt
   212809630 Jun  4 15:32 .../enwiki-20190601-pages-articles-multistream-index.txt.bz2
 17142482823 Jun  4 15:30 .../enwiki-20190601-pages-articles-multistream.xml.bz2

https://github.com/earwig/mwparserfromhell
https://mwparserfromhell.readthedocs.io/en/latest/index.html
'''
import datetime
import os

import bottle

import addons.mywiki.wikidb as wikidb

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
        results = wikidb.get_search_results(query)
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
    article, source, short_description = wikidb.get_article(name, query)
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
        results = wikidb.get_search_results(name)
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
