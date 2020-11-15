import argparse
import quopri


class VCFGenerator:
    """ Converts txt-based contact list into vcf contacts file recognized by Android. """
    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--input', type=str, help='input ".txt" file', required=True)
        parser.add_argument('--output', type=str, help='output ".vcf" file', required=True)
        args = parser.parse_args()

        return args.input, args.output

    def main(self):
        input_file_path, output_file_path = self.parse_args()
        vcards = []
        with open(input_file_path, 'tr') as txt:
            name = ''
            surname = ''
            phones = []
            for line in txt:
                if line[0] not in (' ', '\n'):
                    if phones:
                        vcards.append((name, surname, phones))
                    parts = line.split(' ', maxsplit=1)
                    name = parts[0].strip()
                    surname = parts[1].strip() if len(parts) > 1 else ''
                    phones = []
                else:
                    if line.strip().startswith('+'):
                        phones.append(line.strip())
            if phones:
                vcards.append((name, surname, phones))

        with open(output_file_path, 'tw') as vcf:
            for name, surname, phones in vcards:
                vcf.write('BEGIN:VCARD\n')
                vcf.write('VERSION:2.1\n')
                vcf.write('N;CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:{}\n'.format(
                    quopri.encodestring('{};{};;;'.format(surname, name).encode()).decode()
                ))
                vcf.write('FN;CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:{}\n'.format(
                    quopri.encodestring('{} {}'.format(name, surname).encode()).decode()
                ))
                for phone in phones:
                    vcf.write('TEL;CELL:{}\n'.format(phone))
                vcf.write('END:VCARD\n')


def main():
    VCFGenerator().main()


if __name__ == '__main__':
    main()
