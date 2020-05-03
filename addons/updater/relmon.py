import datetime
import getpass
import json
import os
import sqlite3

import addons.updater.versions as versions
import addons.updater.repo as repo

DB = os.path.expanduser(os.path.join('~{}'.format(getpass.getuser()), '.data', 'databases', 'relmon.db'))

index = {}


def get_version(package, rules, ignores, series):
    if 'versions' not in package:
        if 'version' in package \
                and versions.check_rules(package['version'], rules) \
                and package['version'] not in ignores \
                and (not series or repo.Tag(package['version']).check_series(repo.Tag(series))):
            return versions.apply_rules(package['version'], rules)
        return ''
    else:
        for version in package['versions']:
            if versions.check_rules(version, rules) \
                    and version not in ignores \
                    and (not series or repo.Tag(version).check_series(repo.Tag(series))):
                return versions.apply_rules(version, rules)
    return ''


def get_relmon_version(relmon_id, rules, ignores, series):
    rules = rules.split(',')

    version = None
    try:
        package_id = int(relmon_id)
        if package_id in index:
            version = get_version(index[package_id], rules, ignores, series)
        else:
            old_date = datetime.datetime(1970, 1, 1)

            conn = sqlite3.connect(DB)
            try:
                c = conn.cursor()
                c.execute('''
                    insert into package(id, info, updated)
                        values (?, ?, ?)
                    on conflict(id) do
                        update set updated = ?
                    ''', (package_id, None, old_date, old_date))
            except sqlite3.OperationalError:
                pass
            finally:
                conn.commit()
                conn.close()
    except ValueError:
        pass

    return version


def rebuild_index():
    conn = sqlite3.connect(DB)
    try:
        c = conn.cursor()
        c.execute('select id, info from package')
        for row in c.fetchall():
            if row[1] is not None:
                index[row[0]] = json.loads(row[1])
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()


rebuild_index()
