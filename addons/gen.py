import sys
import secrets


def gen():
    if len(sys.argv) > 1 and sys.argv[1] == "pass":
        c = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ~`!@#$%^&*()-_+=\\|{}[]:;\"',./?><"
        s = ""
        rnd = secrets.SystemRandom()
        for i in range(0, 12):
            s += rnd.choice(c)
        print(s)
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "longpass":
        c = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_"
        s = ""
        rnd = secrets.SystemRandom()
        for i in range(0, 50):
            s += rnd.choice(c)
        print(s)
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "word":
        c = "aeiou"
        v = "bcdfghjklmnpqrstvwxzy"

        # numbers from http://www.math.cornell.edu/~mec/2003-2004/cryptography/subs/frequencies.html
        c_freq = [14810, 21912, 13318, 14003, 5246]
        v_freq = [2715, 4943, 7874, 4200, 3693, 10795, 188, 1257,
                7253, 4761, 12666, 3316, 205, 10977, 11450, 16587,
                2019, 3819, 315, 128, 3853]

        rnd = secrets.SystemRandom()

        def random_letter(letters, freqs):
            roll = rnd.randint(1, sum(freqs))
            roll -= freqs[0]
            i = 0
            while (roll > 0):
                i += 1
                roll -= freqs[i]
            return letters[i]

        def random_v():
            return random_letter(v, v_freq)

        def random_c():
            return random_letter(c, c_freq)

        l_repeat = [100, 99, 96, 92, 90, 70, 50, 30, 20, 10, 6]
        c_repeat = [35]
        v_repeat = [60, 6]

        c_start = 25

        default_repeat = 4

        for i in range(10000):
            l_repeat.append(default_repeat)
            c_repeat.append(default_repeat)
            v_repeat.append(default_repeat)

        length = 0
        word = ""
        cnt = 0
        c_was = False
        while (True):
            roll = rnd.randint(1, 100)
            if roll > l_repeat[length] and c_was:
                break
            if length == 0:
                roll = rnd.randint(1, 100)
                if (roll > c_start):
                    word += random_v()
                    prev = 'v'
                    cnt = 1
                else:
                    word += random_c()
                    prev = 'c'
                    cnt = 1
                    c_was = True
            else:
                if prev == 'v':
                    roll = rnd.randint(1, 100)
                    if roll <= v_repeat[cnt - 1]:
                        word += random_v()
                        cnt += 1
                    else:
                        word += random_c()
                        prev = 'c'
                        cnt = 1
                        c_was = True
                else:
                    roll = rnd.randint(1, 100)
                    if roll <= c_repeat[cnt - 1]:
                        word += random_c()
                        cnt += 1
                        c_was = True
                    else:
                        word += random_v()
                        prev = 'v'
                        cnt = 1
            length += 1
        print(word)
        sys.exit(0)

    print("usage:")
    print("    gen pass")
    print("  or:")
    print("    gen longpass")
    print("  or:")
    print("    gen word")
