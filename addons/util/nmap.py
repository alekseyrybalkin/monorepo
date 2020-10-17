import argparse
import concurrent.futures
import socket


class Nmap:
    """ see https://stackoverflow.com/questions/26174743/making-a-fast-port-scanner """
    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('url', type=str)
        parser.add_argument('--max-port', type=int, default=1000)
        parser.add_argument('--max-workers', type=int, default=500)
        return parser.parse_args()

    def scanport(self, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.4)

        try:
            con = s.connect((self.args.url, port))
            print('{:<10}open  {}'.format('{}/tcp'.format(port), self.tcp_services.get(port)))
            con.close()
        except Exception as e:
            pass

    def read_tcp_services(self):
        tcp_services = {}
        with open('/etc/services', 'tr') as etc_services:
            for line in etc_services:
                parts = line.split()
                if len(parts) > 1 and '/tcp' in parts[1]:
                    port = int(parts[1].replace('/tcp', ''))
                    tcp_services[port] = parts[0]
        return tcp_services

    def main(self):
        self.args = self.parse_args()
        self.tcp_services = self.read_tcp_services()

        print('PORT      STATE SERVICE')
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.args.max_workers) as executor:
            for port in range(1, self.args.max_port + 1):
                executor.submit(self.scanport, port)


def main():
    Nmap().main()


if __name__ == '__main__':
    main()
