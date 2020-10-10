import itertools

import addons.heaven.util


class GenDomains:
    def write_etc_hosts(self, domains):
        header = ''
        with open('/etc/hosts', 'tr') as conf_file:
            for line in conf_file:
                if not line.startswith('127.0.0.1   '):
                    header += line

        with open('/etc/hosts', 'tw') as conf_file:
            conf_file.write(header)

            for domain in domains:
                conf_file.write('127.0.0.1   {}\n'.format(domain))
                conf_file.write('127.0.0.1   www.{}\n'.format(domain))

    def write_tinyproxy_conf(self, domains):
        header = ''
        with open('/etc/tinyproxy/tinyproxy.conf', 'tr') as conf_file:
            for line in conf_file:
                if not line.startswith('upstream http'):
                    header += line

        with open('/etc/tinyproxy/tinyproxy.conf', 'tw') as conf_file:
            conf_file.write(header)

            for domain in domains:
                conf_file.write('upstream http 127.0.0.1:7997 "{}"\n'.format(domain))
                conf_file.write('upstream http 127.0.0.1:7997 ".{}"\n'.format(domain))

            conf_file.write('upstream http 127.0.0.1:7997 "."\n')

    def main(self):
        config = addons.heaven.util.local_read_json('domains')

        self.write_etc_hosts(itertools.chain(*config['blacklist'].values()))
        self.write_tinyproxy_conf(itertools.chain(*config['blacklist'].values()))

        shell.run('systemctl restart tinyproxy')


def main():
    GenDomains().main()


if __name__ == '__main__':
    main()
