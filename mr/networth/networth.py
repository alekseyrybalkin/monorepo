import argparse
import copy
import datetime
import math
import os
import sys

import mr.config
import mr.shell as shell


class NetworthCalculator:
    def __init__(self):
        self.args = self.parse_args()
        self.config = mr.config.Config('networth').read()
        self.networth_data = self.config['networth_data']
        for item in self.networth_data:
            for field in ['date', 'currency_exchange_rate_date']:
                item[field] = datetime.datetime.strptime(item[field], '%d.%m.%Y').date()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--predict', action='store_true')
        return parser.parse_args()

    def get_total_rub(self, data):
        total_rub = 0
        for bank in self.config['banks']:
            for account in bank['accounts']:
                key = '{}_{}'.format(bank['alias'], account['name'])
                if account['currency'] == 'rub':
                    total_rub += data.get(key, 0)

        total_rub += data.get('cash', 0)
        total_rub += data.get('business_account', 0)
        total_rub -= data.get('fns_bound', 0)
        total_rub -= data.get('pfr_bound', 0)

        return total_rub

    def get_total_usd(self, data):
        total_usd = 0
        for bank in self.config['banks']:
            for account in bank['accounts']:
                key = '{}_{}'.format(bank['alias'], account['name'])
                if account['currency'] == 'usd':
                    total_usd += data.get(key, 0) * data.get('usd_exchange_rate', 1)

        total_usd += data.get('cash_usd', 0) * data.get('usd_exchange_rate', 1)

        return total_usd

    def get_total_euro(self, data):
        total_euro = 0
        for bank in self.config['banks']:
            for account in bank['accounts']:
                key = '{}_{}'.format(bank['alias'], account['name'])
                if account['currency'] == 'eur':
                    total_euro += data.get(key, 0) * data.get('euro_exchange_rate', 1)

        total_euro += data.get('cash_euro', 0) * data.get('euro_exchange_rate', 1)

        return total_euro

    def process_data(self, data):
        total_rub = self.get_total_rub(data)
        total_usd = self.get_total_usd(data)
        total_euro = self.get_total_euro(data)

        total = total_rub + total_usd + total_euro

        bank_totals = {}
        for bank in self.config['banks']:
            bank_total = 0
            for account in bank['accounts']:
                key = '{}_{}'.format(bank['alias'], account['name'])
                if account['currency'] == 'rub':
                    bank_total += data.get(key, 0)
                elif account['currency'] == 'usd':
                    bank_total += data.get(key, 0) * data.get('usd_exchange_rate', 1)
                elif account['currency'] == 'eur':
                    bank_total += data.get(key, 0) * data.get('euro_exchange_rate', 1)
            if bank_total:
                bank_totals[bank['alias']] = bank_total

        total_in_usd = total / data.get('usd_exchange_rate', 1)
        total_in_euro = total / data.get('euro_exchange_rate', 1)

        lent_rub = data.get('lent', 0)
        lent_usd = data.get('lent_usd', 0) * data.get('usd_exchange_rate', 1)
        lent_euro = data.get('lent_euro', 0) * data.get('euro_exchange_rate', 1)
        percent_lent = (lent_rub + lent_usd + lent_euro) / total * 100

        total_crypto = 0
        for crypto in self.config['crypto']:
            key = '{}_exchange_rate'.format(crypto)
            total_crypto += data.get(crypto, 0) * data.get(key, 1) * data.get('usd_exchange_rate', 1)
        percent_crypto = total_crypto / total * 100

        interest = 0
        for bank in self.config['banks']:
            for account in bank['accounts']:
                if account['interest']:
                    if account['currency'] == 'rub':
                        amount = data.get('{}_{}'.format(bank['alias'], account['name']), 0)
                        percent = data.get('{}_{}_percent'.format(bank['alias'], account['name']), 0)
                        interest += amount * percent
                    elif account['currency'] == 'usd':
                        amount = data.get('{}_{}'.format(bank['alias'], account['name']), 0)
                        percent = data.get('{}_{}_percent'.format(bank['alias'], account['name']), 0)
                        interest += amount * percent * data.get('usd_exchange_rate', 1)
                    elif account['currency'] == 'eur':
                        amount = data.get('{}_{}'.format(bank['alias'], account['name']), 0)
                        percent = data.get('{}_{}_percent'.format(bank['alias'], account['name']), 0)
                        interest += amount * percent * data.get('euro_exchange_rate', 1)

        if data['date'] >= datetime.date(2021, 1, 1) and interest > 60000:
            interest -= (interest - 60000) * 0.13

        interest /= 12

        data['total'] = total
        data['bank_totals'] = bank_totals
        data['total_in_usd'] = total_in_usd
        data['total_in_euro'] = total_in_euro
        data['total_rub'] = total_rub
        data['total_usd'] = total_usd
        data['total_euro'] = total_euro
        data['percent_lent'] = percent_lent
        data['percent_crypto'] = percent_crypto
        data['interest'] = interest

    def print_header(self):
        header = (
            '    Date   |'
            '      Total      |'
            '      USD     |'
            '      EUR     |'
            '      ₽ / $ / €     |'
            '    Lent %   |'
            '   Crypto %  |'
            '    Interest'
        )

        print('-' * 125)
        print(shell.colorize(header))
        print('-' * 125)

    def print_data(
        self,
        data,
        max_total=None,
        max_total_in_usd=None,
        max_total_in_euro=None,
        min_lent=None,
        max_interest=None,
    ):
        total = '{:>15,.2f}'.format(data['total'])
        total_in_usd = '{:>12,.2f}'.format(data['total_in_usd'])
        total_in_euro = '{:>12,.2f}'.format(data['total_in_euro'])
        rub_usd_eur = ' {:2,.1f}  {:4,.1f}  {:4,.1f} '.format(
            data['total_rub'] * 100 / data['total'],
            data['total_usd'] * 100 / data['total'],
            data['total_euro'] * 100 / data['total'],
        )
        percent_lent = '{:>10.2f}%'.format(data['percent_lent'])
        percent_crypto = '{:>10.2f}%'.format(data['percent_crypto'])
        interest = '{:>+12,.2f}'.format(data['interest'])

        if data['total'] == max_total:
            total = shell.colorize(total, 2)
        if data['total_in_usd'] == max_total_in_usd:
            total_in_usd = shell.colorize(total_in_usd, 2)
        if data['total_in_euro'] == max_total_in_euro:
            total_in_euro = shell.colorize(total_in_euro, 2)
        if data['percent_lent'] == min_lent:
            percent_lent = shell.colorize(percent_lent, 2)
        if data['interest'] == max_interest:
            interest = shell.colorize(interest, 2)

        if data['total_rub'] == 0:
            rub_usd_eur = ' ' * 18
        if data['percent_lent'] == 0:
            percent_lent = ' ' * 11
        if data['percent_crypto'] == 0:
            percent_crypto = ' ' * 11
        if data['interest'] == 0:
            interest = ' ' * 11

        line = '{:>10} | {} | {} | {} | {} | {} | {} | {}'.format(
            data.get('date').strftime('%Y-%b'),
            total,
            total_in_usd,
            total_in_euro,
            rub_usd_eur,
            percent_lent,
            percent_crypto,
            interest,
        )
        sys.stdout.write(line + '\n')

    def find_max_values(self, data_array):
        max_total = 0
        max_total_in_usd = 0
        max_total_in_euro = 0
        min_lent = 1e100
        max_interest = 0

        for data in data_array:
            if data['date'].day == 1:
                if data['total'] > max_total:
                    max_total = data['total']
                if data['total_in_usd'] > max_total_in_usd:
                    max_total_in_usd = data['total_in_usd']
                if data['total_in_euro'] > max_total_in_euro:
                    max_total_in_euro = data['total_in_euro']
                if data['percent_lent'] < min_lent:
                    min_lent = data['percent_lent']
                if data['interest'] > max_interest:
                    max_interest = data['interest']

        return max_total, max_total_in_usd, max_total_in_euro, min_lent, max_interest

    def show_historical_data(self):
        for data in self.networth_data:
            self.process_data(data)

        self.print_header()
        for data in reversed(self.networth_data):
            self.print_data(data, *self.find_max_values(self.networth_data))
        self.print_header()

        sum_all_banks = sum(bank_total for bank_total in self.networth_data[0]['bank_totals'].values())
        rest = self.networth_data[0]['total'] - sum_all_banks
        bank_data = [
            (
                '{}:'.format(bank['name']),
                self.networth_data[0]['bank_totals'][bank['alias']],
                self.networth_data[0]['bank_totals'][bank['alias']] * 100 / self.networth_data[0]['total'],
            )
            for bank in self.config['banks'] if bank['alias'] in self.networth_data[0]['bank_totals']
        ]
        bank_data.append(('', rest, rest * 100 / self.networth_data[0]['total']))

        bank_lines = ['{:>9} {:>12,.2f} {:>5,.1f}%'.format(*data) for data in bank_data]
        if len(bank_lines) % 2 != 0:
            bank_lines.append('')

        print()
        for i in range(int(math.ceil(len(bank_lines) / 2))):
            if i == 0:
                print('  {:>12,.2f}:  {}     {}'.format(
                    self.networth_data[0]['total'],
                    bank_lines[i],
                    bank_lines[len(bank_lines) // 2 + i],
                ))
            else:
                print('  {:>12}   {}     {}'.format(
                    '',
                    bank_lines[i],
                    bank_lines[len(bank_lines) // 2 + i],
                ))

    def show_predicted_data(self):
        start = 0
        for data in self.networth_data:
            if data['date'].day != 1:
                start += 1

        self.networth_data = self.networth_data[start:]

        interest_6 = sum(d['interest'] for d in self.networth_data[:6])
        interest_12 = sum(d['interest'] for d in self.networth_data[:12])
        monthly_increase_6 = (self.networth_data[0]['total'] - self.networth_data[6]['total'] - interest_6) / 6
        monthly_increase_12 = (self.networth_data[0]['total'] - self.networth_data[12]['total'] - interest_12) / 12
        monthly_increase = monthly_increase_12

        print()
        print(' 6 month average increase (minus interest): {:,.2f}'.format(monthly_increase_6))
        print('12 month average increase (minus interest): {:,.2f}    (used in projections below)'.format(
            monthly_increase_12,
        ))

        projected_data = []

        data = copy.copy(self.networth_data[0])
        date = self.networth_data[0]['date']
        while date < datetime.date(2023, 1, 1):
            date = date + datetime.timedelta(days=1)
            while date.day > 1:
                date = date + datetime.timedelta(days=1)

            data['date'] = date

            for bank in self.config['banks']:
                for account in bank['accounts']:
                    key = '{}_{}'.format(bank['alias'], account['name'])
                    if account['interest'] and key in data:
                        amount = data[key]
                        percent = data['{}_percent'.format(key)]
                        data[key] = amount * (1 + percent / 12)
                        if account.get('main', False):
                            data[key] += monthly_increase

            projected_data.append(data)

            data = copy.copy(data)

        for data in projected_data:
            self.process_data(data)
            data['total_rub'] = 0

        print('-' * 125)
        for data in projected_data:
            if data['date'].month == 1:
                self.print_data(data, *self.find_max_values(projected_data))
        print('-' * 125)

    def main(self):
        os.system('clear')

        self.show_historical_data()

        if self.args.predict:
            self.show_predicted_data()


def main():
    NetworthCalculator().main()


if __name__ == '__main__':
    main()
