import sys
import os

import mr.config
import mr.shell as shell


class Things:
    def __init__(self):
        self.config = mr.config.Config('things').read()
        self.main_list = self.config['main_list']
        self.secondary_list_1 = self.config['secondary_list_1']
        self.secondary_list_2 = self.config['secondary_list_2']
        self.bonus_list = self.config['bonus_list']

    def main(self):
        os.system('clear')

        max_len = 29

        sum1 = sum(item[2] * item[1] for item in self.main_list if len(item) > 2)
        sum2 = sum(item[2] * item[1] for item in self.secondary_list_1 if len(item) > 2)
        sum3 = sum(item[2] * item[1] for item in self.secondary_list_2 if len(item) > 2)
        sum4 = sum(item[2] * item[1] for item in self.bonus_list if len(item) > 2)

        print('-' * 169)
        line = '| {:<29s}{:>6} {:>3} | {:<20s}{:>6} {:>3} | {:<20s}{:>6} {:>3} | {:<20s}{:>15} {:>3} |'.format(
                shell.colorize('{:<29s}'.format('Main')),
                shell.colorize('{:>6}'.format(sum1)),
                shell.colorize('{:>3}'.format(sum(item[1] for item in self.main_list))),
                shell.colorize('{:<20s}'.format('Secondary #1')),
                shell.colorize('{:>6} / {:>6}'.format(sum2, sum1 + sum2)),
                shell.colorize('{:>3}'.format(sum(item[1] for item in self.secondary_list_1))),
                shell.colorize('{:<20s}'.format('Secondary #2')),
                shell.colorize('{:>6} / {:>6}'.format(sum3, sum1 + sum2 + sum3)),
                shell.colorize('{:>3}'.format(sum(item[1] for item in self.secondary_list_2))),
                shell.colorize('{:<20s}'.format('Bonus')),
                shell.colorize('{:>6} / {:>6}'.format(sum4, sum1 + sum2 + sum3 + sum4)),
                shell.colorize('{:>3}'.format(sum(item[1] for item in self.bonus_list))),
        )
        print(line)
        print('-' * 169)

        longest = max(
            len(self.main_list),
            len(self.secondary_list_1),
            len(self.secondary_list_2),
            len(self.bonus_list)
        )

        for i in range(longest):
            columns = []
            for lst in [self.main_list, self.secondary_list_1, self.secondary_list_2, self.bonus_list]:
                if i < len(lst):
                    if lst[i][0] == '-':
                        columns.append('-' * 39)
                    else:
                        columns.append('{:<29s}{:>6} {:>3}'.format(
                            lst[i][0][:max_len],
                            lst[i][2] if len(lst[i]) > 2 else '',
                            lst[i][1] if lst[i][1] > 0 else '',
                        ))
                else:
                    columns.append(' ' * 39)

            line = '| {} | {} | {} | {} |'.format(*columns)
            print(line)

        print('-' * 169)


def main():
    Things().main()


if __name__ == '__main__':
    main()
