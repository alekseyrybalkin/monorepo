import getpass
import hashlib
import itertools
import sys
import subprocess

import mr.config


class Service:
    def __init__(self, email, username, service, length=32, comment=None, override=None, version=None):
        self.email = email
        self.username = username
        self.service = service
        self.length = length
        self.comment = comment
        self.override = override
        self.version = version


class Kopass:
    def __init__(self):
        self.config = mr.config.Config('kopass').read()

    def convert(self, number):
        if (number == 0):
            return "0"
        else:
            rest = self.convert(number // len(self.config['symbols'])).lstrip("0")
            return rest + self.config['symbols'][number % len(self.config['symbols'])]

    def normalize(self, hasher):
        return self.convert(int(hasher.hexdigest(), 16))

    def main(self):
        services = [Service(**json_service) for json_service in itertools.chain(*self.config['services'].values())]

        try:
            service = getpass.getpass("Service: ")
            encoded = service.encode("ascii", "ignore")
        except KeyboardInterrupt as _:
            print('')
            sys.exit()

        known_service = None
        cut = 30
        for s in services:
            if service.endswith(s.service):
                cut = s.length - 2
                known_service = s
                break

        if known_service is not None and known_service.version is not None:
            encoded += str(known_service.version).encode('ascii')

        for _ in range(450):
            hasher = hashlib.sha512()
            hasher.update(encoded)
            encoded = self.normalize(hasher).encode("ascii", "ignore")

        if known_service is not None and known_service.override is not None:
            encoded = known_service.override.encode("ascii", "ignore")
            cut = known_service.length

        if len(sys.argv) == 1:
            # chromium needs 4 loops for some reason
            subprocess.run(
                ['xclip', '-selection', 'clipboard', '-loops', '4'],
                input=encoded[:cut].decode("UTF-8"),
                encoding='UTF-8',
            )
            if known_service is not None and known_service.comment is not None:
                print(known_service.comment)
        elif sys.argv[1] in ['-p', '--print']:
            print(encoded[:cut].decode("UTF-8"))


def main():
    Kopass().main()


if __name__ == '__main__':
    main()
