import json

import addons.relmon
import addons.updater.versions as versions
import addons.updater.repo as repo


class RelmonChecker:
    def __init__(self, db):
        self.relmon = addons.relmon.Relmon(db)
        self.rebuild_index()

    def get_version(self, package, rules, ignores, series):
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

    def get_relmon_version(self, relmon_id, rules, ignores, series):
        rules = rules.split(',')

        version = None
        try:
            package_id = int(relmon_id)
            if package_id in self.index:
                version = self.get_version(self.index[package_id], rules, ignores, series)
            else:
                self.relmon.add_cached_placeholder(package_id)
        except ValueError:
            pass

        return version

    def rebuild_index(self):
        self.index = {}
        for row in self.relmon.get_all_packages():
            if row['info'] is not None:
                self.index[row['id']] = json.loads(row['info'])
