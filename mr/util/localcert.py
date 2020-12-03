import argparse
import glob
import os
import shutil
import tempfile

import mr.config
import mr.shell as shell


class LocalCertificateManager:
    def __init__(self):
        self.args = self.parse_args()
        if self.args.command not in ('genroot', 'gendomain', 'trust'):
            raise ValueError('unknown command {}'.format(self.args.command))
        if self.args.command == 'gendomain' and not self.args.domain:
            raise ValueError('command gendmain requires --domain')

        self.config = mr.config.Config(
            'localcert',
            defaults={'local-cert-location': 'etc/ssl/local'},
        ).read()
        self.common_config = mr.config.Config('common').read()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('command', type=str)
        parser.add_argument('--domain', type=str)
        return parser.parse_args()

    def genroot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with shell.popd(tmpdir):
                org = self.config['organization']
                shell.run(f'openssl genpkey -algorithm RSA -out {org}.key')
                shell.run(f'openssl req -x509 -key {org}.key -out {org}.crt.pem -days 3650 -subj /CN={org}/O={org}')

                if os.path.isfile('/usr/bin/trust') and os.path.isdir('/etc/ca-certificates/trust-source/anchors'):
                    shell.run(f'sudo cp {org}.crt.pem /etc/ca-certificates/trust-source/anchors/')
                    shell.run('sudo trust extract-compat')
                else:
                    shutil.move(
                        f'{org}.crt.pem',
                        os.path.join(
                            self.common_config['configs-path'],
                            'base',
                            self.config['local-cert-location'],
                            f'{org}.crt.pem',
                        ),
                    )

                secret_dir = os.path.join(self.common_config['secrets-path'], org)
                os.makedirs(secret_dir, exist_ok=True)
                shutil.move(f'{org}.key', os.path.join(secret_dir, f'{org}.key'))
        print('now update configs, update nss and restart nginx')

    def gendomain(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with shell.popd(tmpdir):
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
                    os.path.join(self.common_config['secrets-path'], org, f'{org}.key'),
                    '-CAserial',
                    os.path.join(self.common_config['secrets-path'], org, f'{org}.srl'),
                    '-CAcreateserial',
                    '-extfile',
                    'extfile',
                ])

                keys_dir = os.path.join(
                    self.common_config['sandbox-path'],
                    self.config['nginx-keys-path'],
                )
                os.makedirs(keys_dir, exist_ok=True)
                shutil.move(f'{domain}.crt', os.path.join(keys_dir, f'{domain}.crt'))
                shutil.move(f'{domain}.key', os.path.join(keys_dir, f'{domain}.key'))

                secret_dir = os.path.join(self.common_config['secrets-path'], org)
                os.makedirs(secret_dir, exist_ok=True)
                shutil.move(f'{domain}.csr', os.path.join(secret_dir, f'{domain}.csr'))
        print('new certificates are in a sandbox')

    def trust(self):
        for cert in glob.iglob(os.path.join('/', self.config['local-cert-location'], '*.pem')):
            fingerprint = shell.output(
                [
                    'openssl',
                    'x509',
                    '-in',
                    cert,
                    '-text',
                    '-fingerprint',
                ],
                silent=False,
            )
            shell.run_with_input(
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
