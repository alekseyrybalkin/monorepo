import argparse
import zipfile


class UnZip:
    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('file', type=str)
        return parser.parse_args()

    def unzip(self, archive_path, dest_dir=None):
        with zipfile.ZipFile(archive_path, 'r') as archive:
            archive.extractall(path=dest_dir)

    def main(self):
        args = self.parse_args()
        self.unzip(args.file)


def main():
    UnZip().main()


if __name__ == '__main__':
    main()
