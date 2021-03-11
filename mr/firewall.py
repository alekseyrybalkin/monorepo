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


def write_iptables_config(conf_file_name, firewall_config):
    header = ''
    with open(conf_file_name, 'tr') as conf_file:
        for line in conf_file:
            if not line.startswith('-A OUTPUT') and not line.strip() == 'COMMIT':
                header += line

    with open(conf_file_name, 'tw') as conf_file:
        conf_file.write(header)

        for uid in firewall_config['no_network_users']:
            conf_file.write('-A OUTPUT -m owner --uid-owner {} -j DROP\n'.format(uid))

        for uid in firewall_config['only_lan_users']:
            conf_file.write('-A OUTPUT -o lo -m owner --uid-owner {} -j ACCEPT\n'.format(uid))
            conf_file.write('-A OUTPUT -d 127.0.0.0/24 -m owner --uid-owner {} -j ACCEPT\n'.format(uid))
            conf_file.write('-A OUTPUT -o + -m owner --uid-owner {} -j DROP\n'.format(uid))

        conf_file.write('COMMIT\n')


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
        config = mr.cloud.util.local_read_json('firewall')
    except FileNotFoundError:
        print('no config found, skipping firewall update')
        return
    domains = list(itertools.chain(*config['blacklist'].values()))
    if config.get('firewall_disabled', False):
        domains = []

    write_etc_hosts('/etc/hosts', domains)
    write_tinyproxy_conf('/etc/tinyproxy/tinyproxy.conf', domains)
    shell.run('systemctl restart tinyproxy')


def local_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-remote', action='store_true')
    args = parser.parse_args()

    firewall_manager = mr.util.hostconf.HostConf().get_option('firewall_manager')
    config = mr.config.Config('firewall', user=firewall_manager).read()
    domains = list(itertools.chain(*config['blacklist'].values()))
    if config.get('firewall_disabled', False):
        domains = []

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

        shell.run('sudo cp {} /etc/hosts'.format(hosts_file))
        shell.run('sudo cp {} /etc/tinyproxy/tinyproxy.conf'.format(tp_file))
        shell.run('sudo cp {} /etc/tinyproxy/tinyproxy-tor.conf'.format(tp_tor_file))

        tinyproxy_state = shell.output('systemctl show tinyproxy --property=ActiveState', strip=True)
        if tinyproxy_state == 'ActiveState=active':
            shell.run('sudo systemctl restart tinyproxy')

        tinyproxy_tor_state = shell.output('systemctl show tinyproxy-tor --property=ActiveState', strip=True)
        if tinyproxy_tor_state == 'ActiveState=active':
            shell.run('sudo systemctl restart tinyproxy-tor')

    if not args.no_remote:
        mr.cloud.util.remote_upload_json('firewall', config)
        mr.cloud.util.remote_run('sudo cloud-genfirewall')

    with tempfile.TemporaryDirectory() as tmpdir:
        iptables_config = os.path.join(tmpdir, 'iptables.rules')
        shutil.copyfile('/etc/iptables/iptables.rules', iptables_config)
        write_iptables_config(iptables_config, config)
        shell.run('sudo cp {} /etc/iptables/iptables.rules'.format(iptables_config))
        shell.run('sudo systemctl restart iptables')


if __name__ == '__main__':
    local_main()
