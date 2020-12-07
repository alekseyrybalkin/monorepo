import datetime
import math
import os

import mr.config
import mr.shell as shell


class TaxesCalculator:
    def __init__(self):
        self.config = mr.config.Config('networth').read()

    def calc_pfr_payed_fixed(self, year, quarter, tax_data):
        sum_pfr_fixed = 0
        for q in range(1, quarter + 1):
            sum_pfr_fixed += math.floor(tax_data['pfr_fixed_payments'][year][str(q)])
        sum_ffoms_fixed = 0
        for q in range(1, quarter + 1):
            sum_ffoms_fixed += tax_data['ffoms_fixed_payments'][year][str(q)]
        return sum_pfr_fixed + sum_ffoms_fixed

    def main(self):
        os.system('clear')
        tax_data = self.config['tax_data']

        yearly_remaining_tax = {}
        print('-' * 81)
        print('| год | квартал | получено |    в ФНС   |     1 %     |  ПФР фикс  |  ПФР всего |')
        print('-' * 81)
        prev_pfr_1_percent = 0
        for year in sorted(tax_data['incoming'].keys())[-2:]:
            for quarter in range(1, 5):
                received = sum(sum(tax_data['incoming'][year][str(q)]) for q in range(1, quarter + 1))
                pfr_payed_fixed = self.calc_pfr_payed_fixed(year, quarter, tax_data)
                pfr_payed = pfr_payed_fixed + math.floor(tax_data['pfr_1_percent_payments'][year])
                fns_payed = sum(tax_data['fns_payments'][year][str(q)] for q in range(2, quarter + 1))

                quarter_tax = round(received * 0.06)
                quarter_tax -= round(pfr_payed)
                quarter_tax -= fns_payed
                quarter_tax = max(quarter_tax, 0)

                if quarter == 1 and (int(year) - 1) in yearly_remaining_tax:
                    quarter_tax += yearly_remaining_tax[int(year) - 1] - tax_data['fns_payments'][year]['1']

                pfr_1_percent = max((received - 300000), 0) * 0.01
                if int(year) > int(sorted(tax_data['incoming'].keys())[-2]) and quarter == 1:
                    pfr_1_percent += (prev_pfr_1_percent - tax_data['pfr_1_percent_payments'][year])
                next_year = str(int(year) + 1)
                if next_year in tax_data['pfr_1_percent_payments']:
                    pfr_1_percent -= tax_data['pfr_1_percent_payments'][next_year]
                prev_pfr_1_percent = pfr_1_percent

                pfr_fixed = self.config['tax_data']['fixed_fees'][year] - pfr_payed_fixed

                fns = '{:>12.2f}'.format(quarter_tax)
                pfr = '{:>12.2f}'.format(pfr_1_percent + pfr_fixed)

                today = datetime.date.today()
                if today.year == int(year) and (today.month - 1) // 3 == quarter - 1:
                    fns = shell.colorize(fns, 3)
                    pfr = shell.colorize(pfr, 3)

                print('{:>6} {:>4} {:>15,.2f} {} {:>12.2f} {:>12.2f} {}'.format(
                    year,
                    quarter,
                    received,
                    fns,
                    pfr_1_percent,
                    pfr_fixed,
                    pfr,
                ))

                if quarter == 4:
                    yearly_remaining_tax[int(year)] = quarter_tax


def main():
    TaxesCalculator().main()


if __name__ == '__main__':
    main()
