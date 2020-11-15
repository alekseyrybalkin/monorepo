import addons.config
import addons.cloud.util


class TimersUpdater:
    def main(self):
        config = addons.config.Config('timers').read()
        addons.cloud.util.remote_upload_json('timers', config)
        addons.cloud.util.remote_run('sudo cloud-gentimers')


def main():
    TimersUpdater().main()


if __name__ == '__main__':
    main()
