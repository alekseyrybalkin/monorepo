import argparse
import shutil


class Which:
    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('programname', type=str)
        args = parser.parse_args()
        return args.programname

    def main(self):
        programname = self.parse_args()
        executable = shutil.which(programname)
        if executable:
            print(executable)


def main():
    Which().main()


if __name__ == '__main__':
    main()
