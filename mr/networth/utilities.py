import datetime
import os

import mr.config
import mr.shell as shell


class UtilitiesCalculator:
    def __init__(self):
        self.config = mr.config.Config('networth').read()

    def main(self):
        os.system('clear')
        data = self.config['utilities_data']
        readings = data['readings']

        print('-' * 114)
        print()
        print(shell.colorize('    Price CW:      {:.2f}'.format(data['cold_water_price'])))
        print(shell.colorize('    Proce HW:     {:.2f}'.format(data['hot_water_price'])))
        print(shell.colorize('    Price Drain:    {:.2f}'.format(data['water_drain_price'])))
        print(shell.colorize('    Price ED:       {:.2f}'.format(data['electricity_day_price'])))
        print(shell.colorize('    Price EN:       {:.2f}'.format(data['electricity_night_price'])))
        print()

        print('-' * 141)

        headers = [
            'Date',
            'Cold W',
            'Hot W',
            'E Day',
            'E Night',
            'Sum CW',
            'Sum HW',
            'Sum Drain',
            'Sum ED',
            'Sum EN',
            'Total',
        ]
        print(shell.colorize('|'.join('{:^12}'.format(header) for header in headers)))
        print('-' * 141)
        for i in range(len(readings)):
            r = readings[i]

            sum_cw = 0
            sum_hw = 0
            sum_wd = 0
            sum_ed = 0
            sum_en = 0
            total = 0
            if i > 0:
                sum_cw = (r[1] - readings[i - 1][1]) * data['cold_water_price']
                sum_hw = (r[2] - readings[i - 1][2]) * data['hot_water_price']
                sum_wd = (r[1] + r[2] - readings[i - 1][1] - readings[i - 1][2]) * data['water_drain_price']
                sum_ed = (r[3] - readings[i - 1][3]) * data['electricity_day_price']
                sum_en = (r[4] - readings[i - 1][4]) * data['electricity_night_price']
                total = sum_cw + sum_hw + sum_wd + sum_ed + sum_en

            total_str = '{:>10.2f}'.format(total)
            if i == len(readings) - 1:
                total_str = shell.colorize(total_str, 2)

            line = '|'.join([
                ' {:<10} '.format(datetime.datetime.strptime(r[0], '%d.%m.%Y').date().strftime('%Y-%m-%d')),
                ' {:>10.3f} '.format(r[1]),
                ' {:>10.3f} '.format(r[2]),
                ' {:>10.1f} '.format(r[3]),
                ' {:>10.1f} '.format(r[4]),
                ' {:>10.2f} '.format(sum_cw),
                ' {:>10.2f} '.format(sum_hw),
                ' {:>10.2f} '.format(sum_wd),
                ' {:>10.2f} '.format(sum_ed),
                ' {:>10.2f} '.format(sum_en),
                ' {} '.format(total_str),
            ])
            print(line)

        print('-' * 141)


def main():
    UtilitiesCalculator().main()


if __name__ == '__main__':
    main()
