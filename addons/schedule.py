import sys
import datetime


class Schedule:
    def main(self):
        if len(sys.argv) < 2:
            print(
                "Usage: {} <days, int> [starting delta relative to today, default 0 (today), int]".format(sys.argv[0])
            )
            print("Example: {} 42 0".format(sys.argv[0]))
            sys.exit(0)

        try:
            days = int(sys.argv[1])
        except ValueError as e:
            print("days must be an integer")
            sys.exit(0)

        today = datetime.date.today()
        if len(sys.argv) > 2:
            try:
                delta = int(sys.argv[2])
            except ValueError as e:
                print("delta must be an integer")
                sys.exit(0)
            today += datetime.timedelta(days=delta)

        stamp = (int(today.strftime("%s")) - 1) // 86400
        shift = stamp % days
        print("routines.append(Routine(name='', day_mod={}, day_mod_shift={}))".format(days, shift))


def main():
    Schedule().main()


if __name__ == '__main__':
    main()
