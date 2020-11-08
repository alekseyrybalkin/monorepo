import argparse
import glob
import os
import shutil
import tempfile

import addons.config
import addons.helpers
import addons.shell as shell


class LocalCertificateManager:
    def __init__(self):
        self.args = self.parse_args()
        if self.args.command not in ('genroot', 'gendomain', 'trust'):
            raise ValueError('unknown command {}'.format(self.args.command))
        if self.args.command == 'gendomain' and not self.args.domain:
            raise ValueError('command gendmain requires --domain')

        self.config = addons.config.Config(
            'localcert',
            defaults={'local-cert-location': 'etc/ssl/local'},
        ).read()
        self.common_config = addons.config.Config('common').read()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('command', type=str)
        parser.add_argument('--domain', type=str)
        return parser.parse_args()

    def genroot(self):
        shell.run('sudo true')
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            org = self.config['organization']
            shell.run(f'openssl genpkey -algorithm RSA -out {org}.key')
            shell.run(f'openssl req -x509 -key {org}.key -out {org}.crt.pem -days 3650 -subj /CN={org}/O={org}')

            if addons.helpers.get_host_distro() == 'arch':
                shell.run(f'sudo cp {org}.crt.pem /etc/ca-certificates/trust-source/anchors/')
                shell.run('sudo trust extract-compat')
            elif addons.helpers.get_host_distro() == 'jinni':
                shutil.move(
                    f'{org}.crt.pem',
                    os.path.join(
                        self.common_config['configs-path'],
                        self.config['local-cert-location'],
                        f'{org}.crt.pem',
                    ),
                )
                os.chdir(self.common_config['configs-path'])
                shell.run('bash update.bash')
                os.chdir(tmpdir)
                shell.run('sudo ji u nss')

            nginx_running = 'SubState=running' in shell.run('systemctl show nginx')
            if nginx_running:
                shell.run('sudo systemctl restart nginx')

            secret_dir = os.path.join(self.config['secrets-path'], org)
            os.makedirs(secret_dir, exist_ok=True)
            shutil.move(f'{org}.key', os.path.join(secret_dir, f'{org}.key'))

            os.chdir(old_cwd)

    def gendomain(self):
        shell.run('sudo true')
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            org = self.config['organization']
            domain = self.args.domain
            shell.run(f'openssl genpkey -algorithm RSA -out {domain}.key')
            shell.run(f'openssl req -new -key {domain}.key -out {domain}.csr -subj /CN={domain}/O={org}')

            with open('extfile', 'tw') as extfile:
                extfile.write('basicConstraints = CA:FALSE\n')
                extfile.write('subjectKeyIdentifier = hash\n')
                extfile.write('authorityKeyIdentifier = keyid,issuer\n')
                extfile.write(f'subjectAltName = DNS:{domain}\n')

            shell.run([
                'openssl',
                'x509',
                '-req',
                '-in',
                f'{domain}.csr',
                '-days',
                '3650',
                '-out',
                f'{domain}.crt',
                '-CA',
                os.path.join(
                    '/',
                    self.config['local-cert-location'],
                    f'{org}.crt.pem',
                ),
                '-CAkey',
                os.path.join(self.config['secrets-path'], org, f'{org}.key'),
                '-CAserial',
                os.path.join(self.config['secrets-path'], org, f'{org}.srl'),
                '-CAcreateserial',
                '-extfile',
                'extfile',
            ])

            keys_dir = os.path.join(
                self.common_config['configs-path'],
                self.config['nginx-keys-path'],
            )
            os.makedirs(keys_dir, exist_ok=True)
            shutil.move(f'{domain}.crt', os.path.join(keys_dir, f'{domain}.crt'))
            shutil.move(f'{domain}.key', os.path.join(keys_dir, f'{domain}.key'))

            secret_dir = os.path.join(self.config['secrets-path'], org)
            os.makedirs(secret_dir, exist_ok=True)
            shutil.move(f'{domain}.csr', os.path.join(secret_dir, f'{domain}.csr'))

            os.chdir(self.common_config['configs-path'])
            shell.run('bash update.bash')
            os.chdir(tmpdir)

            nginx_running = 'SubState=running' in shell.run('systemctl show nginx')
            if nginx_running:
                shell.run('sudo systemctl restart nginx')

            os.chdir(old_cwd)

    def trust(self):
        for cert in glob.iglob(os.path.join('/', self.config['local-cert-location'], '*.pem')):
            fingerprint = shell.run([
                'openssl',
                'x509',
                '-in',
                cert,
                '-text',
                '-fingerprint',
            ])
            shell.run(
                [
                    'certutil',
                    '-d',
                    'sql:{}/.pki/nssdb'.format(shell.home()),
                    '-A',
                    '-t',
                    'C,,',
                    '-n',
                    os.path.basename(cert),
                ],
                input_bytes=fingerprint.encode(),
            )

    def main(self):
        if self.args.command == 'genroot':
            self.genroot()
        elif self.args.command == 'gendomain':
            self.gendomain()
        elif self.args.command == 'trust':
            self.trust()


def main():
    LocalCertificateManager().main()


if __name__ == '__main__':
    main()
