import addons.config
import addons.heaven.util


class DomainsUpdater:
    def main(self):
        config = addons.config.Config('domains').read()
        addons.heaven.util.remote_upload_json('domains', config)
        addons.heaven.util.remote_run('sudo heaven-gendomains')


def main():
    DomainsUpdater().main()


if __name__ == '__main__':
    main()
