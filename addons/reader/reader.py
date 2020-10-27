import re
import string
import os

import addons.config
import addons.shell as shell


class ReaderIndexGenerator:
    def __init__(self):
        self.config = addons.config.Config('reader').read()

    def main(self):
        epub_links = ''
        os.makedirs(self.config['epubs_path'], exist_ok=True)

        epub_pairs = []

        for root, dirs, files in os.walk(self.config['library_path']):
            for name in files:
                if name.endswith('.epub'):
                    original_name = name
                    name = re.sub(r'^#', '', name)
                    epub_pairs.append((name, original_name, root))

        for name, original_name, path in sorted(epub_pairs):
            book_name = re.sub(r'\.epub$', '', name)
            if book_name not in self.config['enabled_books']:
                continue
            book_path = os.path.join(self.config['epubs_path'], book_name)
            os.makedirs(book_path, exist_ok=True)
            if not os.path.exists(os.path.join(book_path, 'META-INF')):
                shell.run(['unzip', os.path.join(str(path), original_name), '-d', str(book_path)])

            if book_name in self.config['tocs']:
                toc_path = os.path.join(book_path, self.config['tocs'][book_name])
            else:
                toc_path = book_path
            epub_links += f'<a href="file://{toc_path}">{book_name}</a><br/>\n'

        template_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'reader_index.html')
        with open(template_file_path, 'tr') as template_file:
            template = string.Template(template_file.read())
        with open('/tmp/reader_index.html', 'tw') as reader_index:
            reader_index.write(template.substitute(
                epub_links=epub_links,
            ))


def main():
    ReaderIndexGenerator().main()


if __name__ == '__main__':
    main()
