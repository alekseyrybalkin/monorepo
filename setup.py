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
            'valet = addons.valet:main',
            'schedule = addons.util.schedule:main',
            'timers = addons.timers:main',
            'domains = addons.domains:local_main',
            'heaven-gentimers = addons.heaven.timers:main',
            'heaven-gendomains = addons.domains:heaven_main',
            'backup = addons.backup:main',
            'regen-reader-index = addons.reader.reader:main',
            'which = addons.util.which:main',
            'sss = addons.util.sss:main',
            'genvcf = addons.util.genvcf:main',
            'kopass = addons.util.kopass:main',
        ],
    },
    include_package_data=True,
)
