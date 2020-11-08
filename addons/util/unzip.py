import argparse
import zipfile


class UnZip:
    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('file', type=str)
        return parser.parse_args()

    def main(self):
        args = self.parse_args()

        with zipfile.ZipFile(args.file, 'r') as archive:
            archive.extractall()


def main():
    UnZip().main()


if __name__ == '__main__':
    main()
