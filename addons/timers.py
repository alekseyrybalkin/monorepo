import addons.config
import addons.heaven.util


class TimersUpdater:
    def main(self):
        config = addons.config.Config('timers').read()
        addons.heaven.util.remote_upload_json('timers', config)
        addons.heaven.util.remote_run('sudo heaven-gentimers')


def main():
    TimersUpdater().main()


if __name__ == '__main__':
    main()
