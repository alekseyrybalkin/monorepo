import glob
import os

import addons.heaven.util
import addons.shell as shell


class TimersUpdater:
    def write_service_file(self, timer, service_file):
        service_file.write('[Unit]\n')
        service_file.write('Description=' + timer['desc'] + '\n')
        service_file.write('\n')
        service_file.write('[Service]\n')
        service_file.write('Environment="TERM=screen"\n')
        service_file.write('User=' + timer['user'] + '\n')
        service_file.write('Group=' + timer['group'] + '\n')
        service_file.write('Type=oneshot\n')
        service_file.write('ExecStart=' + timer['task'] + '\n')

    def write_timer_file(self, timer, timer_file):
        timer_file.write('[Unit]\n')
        timer_file.write('Description=' + timer['desc'] + '\n')
        timer_file.write('\n')
        timer_file.write('[Timer]\n')
        timer_file.write('OnCalendar=' + timer['time'] + '\n')
        if timer['delay']:
            timer_file.write('RandomizedDelaySec={}\n'.format(timer['delay']))
        timer_file.write('Persistent=true\n')
        timer_file.write('\n')
        timer_file.write('[Install]\n')
        timer_file.write('WantedBy=timers.target\n')

    def main(self):
        for timer in glob.iglob('/etc/systemd/system/valet*.timer'):
            shell.run('systemctl stop {}'.format(os.path.basename(timer)))
            shell.run('systemctl disable {}'.format(os.path.basename(timer)))

        for systemd_file in glob.iglob('/etc/systemd/system/valet*'):
            os.remove(systemd_file)

        config = addons.heaven.util.read_json('timers')

        for timer in config['timers']:
            service_file_name = os.path.join('/etc/systemd/system', 'valet-{}.service'.format(timer['name']))
            with open(service_file_name, 'tw') as service_file:
                self.write_service_file(timer, service_file)

            timer_file_name = os.path.join('/etc/systemd/system', 'valet-{}.timer'.format(timer['name']))
            with open(timer_file_name, 'tw') as timer_file:
                self.write_timer_file(timer, timer_file)

        shell.run('systemctl daemon-reload')

        for timer in config['timers']:
            shell.run('systemctl enable valet-{}.timer'.format(timer['name']))
            shell.run('systemctl start valet-{}.timer'.format(timer['name']))

        addons.heaven.util.local_remove_json('timers')


def main():
    TimersUpdater().main()


if __name__ == '__main__':
    main()
