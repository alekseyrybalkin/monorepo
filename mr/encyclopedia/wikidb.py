import re
import sqlite3
import sys
import bz2
import os
import copy
import urllib
import xml.etree.ElementTree

import mwparserfromhell as mw
import whoosh.index
import whoosh.qparser
import whoosh.query

import mr.config
import mr.encyclopedia.create_sqlite_index


class WikiDB:
    def __init__(self, db):
        self.db = db
        self.config = mr.config.Config('encyclopedia').read()

    def get_search_results(self, query):
        ix = whoosh.index.open_dir(self.config['whoosh_index'])
        with ix.searcher() as searcher:
            parser = whoosh.qparser.QueryParser("name", ix.schema)
            parser.add_plugin(whoosh.qparser.FuzzyTermPlugin())
            query = parser.parse(query)
            results = searcher.search(query, limit=100)

            return [
                {
                    "rank": i,
                    "percent": 0,
                    "name": row['name'],
                } for i, row in enumerate(results)
            ]

    def get_article(self, name, query):
        res = self.db.select_one('select start_byte, end_byte, idx from wiki_index where name = ?', (name,))
        if res is None:
            res = self.db.select_one(
                'select start_byte, end_byte, idx from wiki_index where name = ?',
                (name.lower().title(),),
            )
            if res is None:
                return None, None, None

        start, end, idx = res['start_byte'], res['end_byte'], res['idx']

        with open(self.config['dump_file'], 'br') as f:
            f.seek(start)
            x = f.read(end - start + 1)
            xml_str = '<xml>' + bz2.decompress(x).decode() + '</xml>'
            data = xml.etree.ElementTree.fromstring(xml_str)

            wikitext = data[idx].find('revision').find('text').text

            parsed = mw.parse(wikitext)

            if wikitext.startswith('#REDIRECT '):
                wikilink = parsed.filter_wikilinks()[0]
                if wikilink.title != name:
                    return 'redirect', wikilink.title, None

            for tag in parsed.ifilter_tags():
                try:
                    if tag.tag == 'ref':
                        parsed.replace(tag, '<span>⚓</span>', recursive=True)
                        continue

                    if tag.tag in ['b', 'blockquote']:
                        parsed.replace(
                            tag,
                            '<{}>{}</{}>'.format(tag.tag, tag.contents, tag.tag),
                            recursive=True,
                        )
                    elif tag.tag not in ['br', 'li']:
                        parsed.replace(
                            tag,
                            '{}'.format(tag.contents),
                            recursive=True,
                        )

                except ValueError:
                    pass

            try:
                parsed.replace('<small>', '')
            except ValueError:
                pass

            for template in parsed.ifilter_templates():
                if str(template.name).lower().strip().startswith('infobox '):
                    replacement = '''
                        <div style="display: inline; float: right; padding: 6px; width: 400px; margin-left: 10px;
                                margin-bottom: 10px;">
                            <table style="line-height: 1.4em; font-size: 1em; border: 1px solid black;
                                    border-collapse: collapse; border-spacing: 0;">
                                <th colspan=2 style="border: 1px solid black;">{}</th>
                                {}
                            </table>
                        </div>
                    '''.format(
                        str(template.name)[8:],
                        ''.join('''
                            <tr>
                                <td style="width: 120px; border: 1px solid black;">{}</td>
                                <td style="border: 1px solid black;">{}</td>
                            </tr>
                        '''.format(
                            str(p.name),
                            str(p.value),
                        ) for p in template.params),
                    )
                    try:
                        parsed.replace(
                            template,
                            replacement,
                            recursive=True,
                        )
                    except ValueError:
                        pass

            for template in parsed.ifilter_templates():
                if str(template.name).lower().strip() == 'quote':
                    replacement = '<blockquote>{}</blockquote>'.format(template.params[0])
                    parsed.replace(
                        template,
                        replacement,
                        recursive=True,
                    )

            short_description = ''
            for template in parsed.ifilter_templates():
                if str(template.name).lower().strip() == 'short description':
                    short_description = template.params[0]
                    parsed.replace(template, '', recursive=True)

            for template in parsed.ifilter_templates():
                try:
                    template.name = template.name.lower().strip()

                    if template.name == 'coord':
                        replacement = '/'.join(str(p) for p in template.params[:6])
                        parsed.replace(
                            template,
                            replacement,
                            recursive=True,
                        )
                except ValueError:
                    pass

            for template in parsed.ifilter_templates():
                try:
                    template.name = template.name.lower().strip()
                    if template.name == 'pp' or template.name.startswith('pp-'):
                        parsed.replace(template, '', recursive=True)
                except ValueError:
                    pass

            for template in parsed.ifilter_templates():
                try:
                    template.name = template.name.lower().strip()
                    if template.name.startswith('cite ') or template.name == 'webarchive' or template.name == 'isbn':
                        if template.has('url'):
                            parsed.replace(
                                template,
                                ' <a href="{}">[_]</a> '.format(template.get('url').value),
                                recursive=True,
                            )
                        else:
                            parsed.replace(template, '', recursive=True)
                except ValueError:
                    pass

            for template in parsed.ifilter_templates():
                try:
                    template.name = template.name.lower().strip()
                    if template.name == 'ipac-en':
                        parsed.replace(
                            template,
                            ''.join(str(p.value) for p in template.params),
                            recursive=True,
                        )
                except ValueError:
                    pass

            for template in parsed.ifilter_templates():
                try:
                    template.name = template.name.lower().strip()
                    if template.name.startswith('lang-'):
                        parsed.replace(
                            template,
                            ' ({}: {}) '.format(
                                str(template.name).replace('lang-', ''),
                                ', '.join(str(p.value) for p in template.params),
                            ),
                            recursive=True,
                        )
                except ValueError:
                    pass

            for template in parsed.ifilter_templates():
                try:
                    template.name = template.name.lower().strip()
                    if template.name == 'lang':
                        parsed.replace(
                            template,
                            '{}: {}'.format(str(template.params[0].value), str(template.params[1].value)),
                            recursive=True,
                        )
                except ValueError:
                    pass

            for template in parsed.ifilter_templates():
                try:
                    template.name = template.name.lower().strip()
                    if template.name == 'convert':
                        parsed.replace(
                            template,
                            ' '.join(str(p.value) for p in template.params[:-1]),
                            recursive=True,
                        )
                except ValueError:
                    pass

            for template in parsed.ifilter_templates():
                try:
                    template.name = template.name.lower().strip()
                    if template.name in ['main', 'main article']:
                        parsed.replace(
                            template,
                            '<div>Main article: <a href="/article?name={}&query={}">{}</a></div>'.format(
                                urllib.parse.quote(str(template.params[0]), safe=''),
                                query,
                                template.params[0],
                            ),
                            recursive=True,
                        )
                except ValueError:
                    pass

            for template in parsed.ifilter_templates():
                try:
                    template.name = template.name.lower().strip()
                    if template.name == 'see also':
                        parsed.replace(
                            template,
                            '<div>See also: <a href="/article?name={}&query={}">{}</a></div>'.format(
                                urllib.parse.quote(str(template.params[0]), safe=''),
                                query,
                                template.params[0],
                            ),
                            recursive=True,
                        )
                except ValueError:
                    pass

            for template in parsed.ifilter_templates():
                try:
                    template.name = template.name.lower().strip()
                    if template.name == 'citation needed':
                        parsed.replace(
                            template,
                            ' [?] ',
                            recursive=True,
                        )
                except ValueError:
                    pass

            for template in parsed.ifilter_templates():
                try:
                    template.name = template.name.lower().strip()
                    content = str(template).strip()
                    if content.find('\n') == -1:
                        parsed.replace(
                            template,
                            '''
                                <div style="display: inline; font-size: 0.9em; color: #d0281a; border: 1px solid black;
                                        border-radius: 16px; padding-left: 6px; padding-right: 6px; padding-top: 2px;
                                        padding-bottom: 2px;">
                                    {}
                                </div>
                            '''.format(template),
                            recursive=False,
                        )
                    else:
                        parsed.replace(
                            template,
                            '''
                                <div style="font-size: 0.9em; color: #d0281a; border: 1px solid black;
                                        border-radius: 16px; margin-top: 6px; margin-bottom: 6px; padding: 6px;">
                                    {}
                                </div>
                            '''.format(template),
                            recursive=False,
                        )
                except ValueError:
                    pass

            for heading in parsed.ifilter_headings():
                if heading.startswith('===='):
                    parsed.replace(heading, '<h4>{}</h4>'.format(str(heading).replace('====', '', 2)), recursive=True)
                elif heading.startswith('==='):
                    parsed.replace(heading, '<h3>{}</h3>'.format(str(heading).replace('===', '', 2)), recursive=True)
                elif heading.startswith('=='):
                    parsed.replace(heading, '<h2>{}</h2>'.format(str(heading).replace('==', '', 2)), recursive=True)
                elif heading.startswith('='):
                    parsed.replace(heading, '<h1>{}</h1>'.format(str(heading).replace('=', '', 2)), recursive=True)

            for wikilink in parsed.ifilter_wikilinks():
                try:
                    title = str(wikilink.title).lower()
                    if title.startswith('file:') or title.startswith('image:'):
                        parsed.replace(wikilink, '<span title="{}">☢</span>'.format(wikilink), recursive=True)
                    parsed.replace(
                        wikilink,
                        '<a href="/article?name={}&query={}">{}</a>'.format(
                            urllib.parse.quote(wikilink.title.encode(), safe=''),
                            query,
                            wikilink.text or wikilink.title,
                        ),
                        recursive=True,
                    )
                except ValueError:
                    pass
            for argument in parsed.ifilter_arguments():
                pass
            for comment in parsed.ifilter_comments():
                parsed.replace(
                    comment,
                    '<span style="color:darkgray;">{}</span>'.format(comment.replace('<!--', '').replace('-->', '')),
                    recursive=True,
                )
            for html_entity in parsed.ifilter_html_entities():
                pass

            parsed = str(parsed)
            parsed = re.sub(r'^\*', '<br/>&nbsp;*&nbsp;', parsed, flags=re.M)

            return parsed, wikitext, short_description
