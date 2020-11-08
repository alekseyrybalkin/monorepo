from setuptools import setup, find_packages

setup(
    name='addons',
    version=1,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'compress-music = addons.util.compress_music:compress',
            'nmap = addons.util.nmap:main',
            'gen = addons.util.gen:gen',
            'srcfetcher = addons.srcfetcher:main',
            'hckrnews = addons.hckrnews.hckrnews:main',
            'relmon = addons.relmon:main',
            'updater = addons.updater.updater:main',
            'r = addons.valet:just_show',
            'd = addons.valet:toggle_done_and_show',
            'schedule = addons.util.schedule:main',
            'timers = addons.timers:main',
            'domains = addons.domains:local_main',
            'heaven-gentimers = addons.heaven.timers:main',
            'heaven-gendomains = addons.domains:heaven_main',
            'backup = addons.backup:main',
            'regen-reader-index = addons.reader.reader:main',
            'which = addons.util.which:main',
            'genvcf = addons.util.genvcf:main',
            'kopass = addons.util.kopass:main',
            'things = addons.util.things:main',
            'networth = addons.networth.networth:main',
            'taxes = addons.networth.taxes:main',
            'utilities = addons.networth.utilities:main',
            'expenses = addons.networth.expenses:main',
            'mpw = addons.util.mpw:main',
            's = addons.util.inspector:main',
            'connect = addons.util.internet:connect',
            'disconnect = addons.util.internet:disconnect',
            'localcert = addons.util.localcert:main',
            'unzip = addons.util.unzip:main',
            'hostconf = addons.util.hostconf:main',
        ],
    },
    include_package_data=True,
)
