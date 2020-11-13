import glob
import os
import tempfile

import addons.config
import addons.shell as shell


class Backuper:
    def rsync(self, src, destdir, exclude=None):
        """ makes a backup of src dir or file into destdir/`basename src` """
        if exclude is None:
            exclude = []
        command = [
            'rsync',
            '-a',
            '--delete',
        ]
        for pattern in exclude:
            command.append('--exclude={}'.format(pattern))
        command.append(src)
        command.append(destdir)

        shell.run(command)

    def sync_as_tarball(self, src, destdir):
        old_cwd = os.getcwd()
        os.chdir(os.path.dirname(src))
        tarfile = os.path.join(destdir, os.path.basename(src) + '.tar')
        shell.run('tar cf {} {}'.format(
            tarfile,
            os.path.basename(src),
        ))
        os.chdir(old_cwd)

    def rsync_encrypted(self, src, destdir, keyfile, exclude=None, compress=False):
        """ makes an encrypted backup of src dir or file into destdir/`basename src`.tar[.gz].gpg """
        with tempfile.TemporaryDirectory() as tmpdir:
            self.rsync(src, tmpdir, exclude)
            with tempfile.TemporaryDirectory() as tmpdir2:
                old_cwd = os.getcwd()
                os.chdir(tmpdir)
                if compress:
                    tarfile = os.path.join(tmpdir2, os.path.basename(src) + '.tar.gz')
                    shell.run('tar cfa {} {}'.format(
                        tarfile,
                        os.path.join(os.path.basename(src)),
                    ))
                else:
                    tarfile = os.path.join(tmpdir2, os.path.basename(src) + '.tar')
                    shell.run('tar cf {} {}'.format(
                        tarfile,
                        os.path.join(os.path.basename(src)),
                    ))
                os.chdir(old_cwd)
                with open(keyfile, 'br') as kf:
                    shell.run_with_input(
                        'gpg --batch -c --passphrase-fd 0 {}'.format(tarfile),
                        input_bytes=kf.read().strip(),
                    )
                self.rsync(tarfile + '.gpg', destdir)

    def main(self):
        config = addons.config.Config('backup').read()

        for rule in config['rules']:
            sources = glob.glob(rule['src']) if '*' in rule['src'] else [rule['src']]
            for src in sources:
                print('{} ==> {}'.format(src, rule['destdir']))
                if not rule.get('encrypt', False):
                    if not rule.get('tarball', False):
                        self.rsync(
                            src,
                            rule['destdir'],
                            exclude=rule.get('exclude', []),
                        )
                    else:
                        if rule.get('exclude', []):
                            raise ValueError('cannot make a tarball with excludes')
                        self.sync_as_tarball(
                            src,
                            rule['destdir'],
                        )
                else:
                    keyfile = rule.get('keyfile', config['keyfile'])
                    self.rsync_encrypted(
                        src,
                        rule['destdir'],
                        keyfile,
                        exclude=rule.get('exclude', []),
                        compress=rule.get('compress', False),
                    )


def main():
    Backuper().main()


if __name__ == '__main__':
    main()
