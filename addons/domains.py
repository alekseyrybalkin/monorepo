import argparse
import itertools
import os
import shutil
import tempfile

import addons.config
import addons.heaven.util
import addons.shell as shell


def write_etc_hosts(conf_file_name, domains):
    header = ''
    with open(conf_file_name, 'tr') as conf_file:
        for line in conf_file:
            if not line.startswith('127.0.0.1        '):
                header += line

    with open(conf_file_name, 'tw') as conf_file:
        conf_file.write(header)

        for domain in domains:
            conf_file.write('127.0.0.1        {}\n'.format(domain))
            conf_file.write('127.0.0.1        www.{}\n'.format(domain))


def write_tinyproxy_conf(conf_file_name, domains):
    header = ''
    with open(conf_file_name, 'tr') as conf_file:
        for line in conf_file:
            if not line.startswith('upstream http 127.0.0.1:7997'):
                header += line

    with open(conf_file_name, 'tw') as conf_file:
        conf_file.write(header)

        for domain in domains:
            conf_file.write('upstream http 127.0.0.1:7997 "{}"\n'.format(domain))
            conf_file.write('upstream http 127.0.0.1:7997 ".{}"\n'.format(domain))

        conf_file.write('upstream http 127.0.0.1:7997 "."\n')


def heaven_main():
    config = addons.heaven.util.local_read_json('domains')
    domains = list(itertools.chain(*config['blacklist'].values()))

    write_etc_hosts('/etc/hosts', domains)
    write_tinyproxy_conf('/etc/tinyproxy/tinyproxy.conf', domains)
    shell.run('systemctl restart tinyproxy')


def local_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-remote', action='store_true')
    args = parser.parse_args()

    config = addons.config.Config('domains', user='rybalkin').read()
    domains = list(itertools.chain(*config['blacklist'].values()))

    with tempfile.TemporaryDirectory() as tmpdir:
        hosts_file = os.path.join(tmpdir, 'hosts')
        tp_file = os.path.join(tmpdir, 'tinyproxy.conf')
        tp_tor_file = os.path.join(tmpdir, 'tinyproxy-tor.conf')

        shutil.copyfile('/etc/hosts', hosts_file)
        shutil.copyfile('/etc/tinyproxy/tinyproxy.conf', tp_file)
        shutil.copyfile('/etc/tinyproxy/tinyproxy-tor.conf', tp_tor_file)

        write_etc_hosts(hosts_file, domains)
        write_tinyproxy_conf(tp_file, domains)
        write_tinyproxy_conf(tp_tor_file, domains)

        shell.run('sudo mv {} /etc/hosts'.format(hosts_file))
        shell.run('sudo mv {} /etc/tinyproxy/tinyproxy.conf'.format(tp_file))
        shell.run('sudo mv {} /etc/tinyproxy/tinyproxy-tor.conf'.format(tp_tor_file))

        if shell.run('systemctl show tinyproxy --property=ActiveState', strip=True, silent=True) == 'ActiveState=active':
            shell.run('sudo systemctl restart tinyproxy')
        if shell.run('systemctl show tinyproxy-tor --property=ActiveState', strip=True, silent=True) == 'ActiveState=active':
            shell.run('sudo systemctl restart tinyproxy-tor')

    if not args.no_remote:
        addons.heaven.util.remote_upload_json('domains', config)
        addons.heaven.util.remote_run('sudo heaven-gendomains')


if __name__ == '__main__':
    local_main()
