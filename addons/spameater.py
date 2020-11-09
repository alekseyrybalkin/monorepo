import addons.config
import addons.heaven.util


class SpamEater:
    def remote_main(self):
        config = addons.heaven.util.local_read_json('spameater')

        filter_types = {
            'header': ':0:',
            'body': ':0B',
        }

        with open('/etc/procmailrc.new', 'w') as out:
            out.write('MAILDIR={}\n'.format(self.config['maildir']))
            out.write('LOGFILE={}\n'.format(self.config['logfile']))
            out.write('VERBOSE={}\n'.format(self.config['verbose']))
            out.write('\n')

            for rule in self.config['filters']:
                for regexp in rule['regexps']:
                    regexp = regexp.strip()
                    if not (regexp.startswith('^') and regexp.endswith('$')):
                        regexp = '^.*{}.*$'.format(regexp)

                    out.write('{}\n'.format(filter_types[rule['type']]))
                    out.write('* {}\n'.format(regexp))
                    if rule['folder'] == '/dev/null':
                        out.write('/dev/null\n')
                    else:
                        out.write('.{}/new\n'.format(rule['folder']))
                    out.write('\n')

    def local_main(self):
        config = addons.config.Config('spameater').read()
        addons.heaven.util.remote_upload_json('spameater', config)
        addons.heaven.util.remote_run('sudo python -m addons.spameater')


def local_main():
    SpamEater().local_main()


if __name__ == '__main__':
    SpamEater().remote_main()
