import re
import string


def check_rules(version, rules):
    if not version:
        return False

    version = version.replace('-', '.')

    if 'no_alpha_skips' not in rules:
        index = 0
        while len(version) > index and version[index] not in string.digits:
            index += 1

        for alpha in string.ascii_letters:
            if alpha in version[index:]:
                return False

    for rule in rules:
        if rule.startswith('skip_'):
            word = rule.replace('skip_', '')
            if word in version:
                return False
        if rule == 'skip_big_third':
            parts = version.split('.')
            if len(parts) >= 3:
                try:
                    if int(parts[2]) > 88:
                        return False
                except ValueError:
                    pass
        if rule == 'skip_big_second':
            parts = version.split('.')
            if len(parts) >= 2:
                try:
                    if int(parts[1]) > 88:
                        return False
                except ValueError:
                    pass
        if rule == 'skip_big_first':
            parts = version.split('.')
            if len(parts) >= 1:
                try:
                    if int(parts[0]) > 300:
                        return False
                except ValueError:
                    pass
        if rule == 'skip_odd_second':
            parts = version.split('.')
            if len(parts) >= 2:
                try:
                    if int(parts[1]) % 2 == 1:
                        return False
                except ValueError:
                    pass
    return True


def apply_rules(version, rules):
    for rule in rules:
        if rule == 'repl_underscore_dot':
            version = version.replace('_', '.')
        if rule == 'repl_tilde_dot':
            version = version.replace('~', '.')
        if rule == 'repl_dash_dot':
            version = version.replace('-', '.')
        if rule.startswith('lstrip_'):
            word = rule.replace('lstrip_', '')
            word = word.replace('-', '.').replace('_', '.')
            version = re.sub('^{}'.format(word), '', version)
    return version
