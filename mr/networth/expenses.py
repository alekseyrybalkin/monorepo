import datetime
import os
import sys

import mr.config
import mr.shell as shell


class ExpensesCalculator:
    def __init__(self):
        self.config = mr.config.Config('networth').read()

    def main(self):
        os.system('clear')
        usd = self.config['networth_data'][0]['usd_exchange_rate']

        year = datetime.date.today().year

        print('-' * 48)
        print('|    Expense         |  Monthly   |   Yearly   |')

        monthly_expenses = self.config['expenses_data']
        mandatory_taxes = self.config['tax_data']['fixed_fees'][str(year)] / 12

        print('-' * 48)
        total = 0
        for group, items in monthly_expenses.items():
            group_total = 0
            for name, details in items.items():
                if details.get('currency', 'rub') == 'usd':
                    details['amount'] *= usd
                total += details['amount']
                group_total += details['amount']
                print('| {:<18} | {:>10,.2f} | {:>10,.2f} |'.format(name, details['amount'], details['amount'] * 12))

            print(shell.colorize(' {:>17} ==> {:>10,.2f} | {:>10,.2f} |'.format(
                group.upper(),
                group_total,
                group_total * 12,
            ), color=6))
            print()

        print(shell.colorize(' {:>17} ==> {:>10,.2f} | {:>10,.2f} |'.format(
            'TAXES',
            mandatory_taxes,
            mandatory_taxes * 12,
        ), color=6))

        print('-' * 48)
        print(shell.colorize('    usd exchange rate:  {:,.2f}'.format(usd)))
        print()
        print(shell.colorize('|   without taxes:      {:,.2f}   {:,.2f} |'.format(total, total * 12)))
        print(shell.colorize('|   WITH TAXES:         {:,.2f}   {:,.2f} |'.format(
            total + mandatory_taxes,
            (total + mandatory_taxes) * 12,
        ), color=6))
        print('-' * 48)


def main():
    ExpensesCalculator().main()


if __name__ == '__main__':
    main()
