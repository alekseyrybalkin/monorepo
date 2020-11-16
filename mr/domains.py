import argparse
import itertools
import os
import shutil
import tempfile

import mr.config
import mr.cloud.util
import mr.shell as shell
import mr.util.hostconf


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


def cloud_main():
    try:
        config = mr.cloud.util.local_read_json('domains')
    except FileNotFoundError:
        print('no local doamins.json found, skipping domains update')
        return
    domains = list(itertools.chain(*config['blacklist'].values()))

    write_etc_hosts('/etc/hosts', domains)
    write_tinyproxy_conf('/etc/tinyproxy/tinyproxy.conf', domains)
    shell.run('systemctl restart tinyproxy')


def local_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-remote', action='store_true')
    args = parser.parse_args()

    firewall_manager = mr.util.hostconf.HostConf().get_option('firewall_manager')
    config = mr.config.Config('domains', user=firewall_manager).read()
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

        tinyproxy_state = shell.output('systemctl show tinyproxy --property=ActiveState', strip=True)
        if tinyproxy_state == 'ActiveState=active':
            shell.run('sudo systemctl restart tinyproxy')

        tinyproxy_tor_state = shell.output('systemctl show tinyproxy-tor --property=ActiveState', strip=True)
        if tinyproxy_tor_state == 'ActiveState=active':
            shell.run('sudo systemctl restart tinyproxy-tor')

    if not args.no_remote:
        mr.cloud.util.remote_upload_json('domains', config)
        mr.cloud.util.remote_run('sudo cloud-gendomains')


if __name__ == '__main__':
    local_main()
