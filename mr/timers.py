import mr.config
import mr.cloud.util


class TimersUpdater:
    def main(self):
        config = mr.config.Config('timers').read()
        mr.cloud.util.remote_upload_json('timers', config)
        mr.cloud.util.remote_run('sudo cloud-gentimers')


def main():
    TimersUpdater().main()


if __name__ == '__main__':
    main()
