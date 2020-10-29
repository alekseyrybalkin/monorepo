import argparse
import os
import tempfile
import time

import addons.config
import addons.shell as shell


class Internet:
    def __init__(self):
        self.args = self.parse_args()
        self.config = addons.config.Config('internet').read()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('command', type=str, default='wired', nargs='?')
        return parser.parse_args()

    def stop(self):
        all_timers = ' '.join('{}.timer'.format(timer) for timer in self.config['timers'])
        shell.run('sudo systemctl stop {}'.format(all_timers))
        time.sleep(self.config['sleep'])

        all_timer_services = ' '.join(self.config['timers'])
        shell.run('sudo systemctl stop {}'.format(all_timer_services))
        time.sleep(self.config['sleep'])

        all_network_services = ' '.join(self.config['network_services'])
        shell.run('sudo systemctl stop {}'.format(all_network_services))
        time.sleep(self.config['sleep'])

        for service in list(self.config['wireless_services'])[::-1]:
            shell.run('sudo systemctl stop {}'.format(service))

        for service in list(self.config['wired_services'])[::-1]:
            shell.run('sudo systemctl stop {}'.format(service))

    def start(self, access_point):
        key = 'wired_services' if self.args.command == 'wired' else 'wireless_services'
        for service, conf in self.config[key].items():
            if conf['enabled']:
                shell.run('sudo systemctl start {}'.format(service))
                time.sleep(self.config['sleep'])

        enabled_network_services = []
        for service, conf in self.config['network_services'].items():
            if not conf['enabled']:
                continue
            enabled_network_services.append(service)
        all_network_services = ' '.join(enabled_network_services)
        shell.run('sudo systemctl start {}'.format(all_network_services))

        enabled_timers = []
        for timer, conf in self.config['timers'].items():
            if not conf['enabled']:
                continue
            if conf.get('high_bandwidth', False) and access_point.get('save_bandwidth', False):
                continue
            enabled_timers.append(timer)
        all_timers = ' '.join('{}.timer'.format(timer) for timer in enabled_timers)
        shell.run('sudo systemctl start {}'.format(all_timers))

    def gen_jinni_environment(self, access_point):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file_path = os.path.join(tmpdir, 'jinni-environment')
            with open(tmp_file_path, 'tw') as tmp_file:
                tmp_file.write('WIRED_DEVICE={}\n'.format(os.environ['WIRED_DEVICE']))
                tmp_file.write('WIFI_DEVICE={}\n'.format(os.environ['WIFI_DEVICE']))
                tmp_file.write('SSID={}\n'.format(access_point['ssid']))
            shell.run('sudo mv {} {}'.format(tmp_file_path, '/run/jinni-environment'))
            shell.run('sudo chown root: {}'.format('/run/jinni-environment'))
            shell.run('sudo chmod 600 {}'.format('/run/jinni-environment'))

    def gen_wpa_supplicant_conf(self, access_point):
        wpa_conf = shell.run([
            'wpa_passphrase',
            access_point['ssid'],
            access_point['pass'],
        ])
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file_path = os.path.join(tmpdir, 'wpa_supplicant.conf')
            with open(tmp_file_path, 'tw') as tmp_file:
                tmp_file.write(wpa_conf)
            shell.run('sudo mv {} {}'.format(tmp_file_path, '/run/wpa_supplicant.conf'))
            shell.run('sudo chown root: {}'.format('/run/wpa_supplicant.conf'))
            shell.run('sudo chmod 600 {}'.format('/run/wpa_supplicant.conf'))

    def main(self):
        if self.args.command == 'stop':
            self.stop()
            return

        access_point = {
            'ssid': '',
        }
        if self.args.command != 'wired':
            alias = self.args.command
            if alias in ('wifi', 'wireless'):
                alias = self.config['wifi']['current_access_point']

            for ap in self.config['wifi']['access_points']:
                if ap.get('alias', ap['ssid']) == alias:
                    access_point = ap

        self.gen_jinni_environment(access_point)
        if self.args.command != 'wired':
            self.gen_wpa_supplicant_conf(access_point)

        self.start(access_point)


def main():
    Internet().main()


if __name__ == '__main__':
    main()
