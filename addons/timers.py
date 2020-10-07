import os
import tempfile

import addons.config
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
        config = addons.config.Config('timers').read()

        with tempfile.TemporaryDirectory() as tmpdir:
            systemd_files = []
            for timer in config['timers']:
                service_file_name = os.path.join(tmpdir, 'valet-' + timer['name'] + '.service')
                timer_file_name = os.path.join(tmpdir, 'valet-' + timer['name'] + '.timer')

                with open(service_file_name, 'tw') as service_file:
                    self.write_service_file(timer, service_file)

                with open(timer_file_name, 'tw') as timer_file:
                    self.write_timer_file(timer, timer_file)

                systemd_files.append(service_file_name)
                systemd_files.append(timer_file_name)

            heaven = os.environ['HEAVEN']
            shell.run([
                'ssh',
                '{}'.format(heaven),
                'rm -rf /tmp/valet; mkdir /tmp/valet',
            ])
            shell.run('rsync -a {} {}:/tmp/valet/'.format(
                ' '.join(systemd_files),
                heaven,
            ))

            remote_logic = '''
                cd /etc/systemd/system;
                for i in valet*.timer; do
                    sudo systemctl stop ${i};
                    sudo systemctl disable ${i};
                done;
                sudo rm -f /etc/systemd/system/valet*;
                sudo mv /tmp/valet/valet* /etc/systemd/system/;
                sudo chown root: /etc/systemd/system/valet*;
                sudo chmod 644 /etc/systemd/system/valet*;
                sudo systemctl daemon-reload;
                for i in valet*.timer; do
                    sudo systemctl enable ${i};
                    sudo systemctl start ${i};
                done;
                sudo systemctl daemon-reload;
                rmdir /tmp/valet;
            '''
            shell.run([
                'ssh',
                '{}'.format(heaven),
                remote_logic,
            ])


def main():
    TimersUpdater().main()


if __name__ == '__main__':
    main()
