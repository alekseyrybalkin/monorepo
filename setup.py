from setuptools import setup, find_packages

setup(
    name='monorepo',
    version=1,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'compress-music = mr.util.compress_music:compress',
            'nmap = mr.util.nmap:main',
            'gen = mr.util.gen:gen',
            'srcfetcher = mr.srcfetcher:main',
            'hckrnews = mr.hckrnews.hckrnews:main',
            'relmon = mr.relmon:main',
            'updater = mr.updater.updater:main',
            'r = mr.valet:just_show',
            'd = mr.valet:toggle_done_and_show',
            'schedule = mr.util.schedule:main',
            'timers = mr.timers:main',
            'domains = mr.domains:local_main',
            'cloud-gentimers = mr.cloud.timers:main',
            'cloud-gendomains = mr.domains:cloud_main',
            'backup = mr.backup:main',
            'regen-reader-index = mr.reader.reader:main',
            'which = mr.util.which:main',
            'genvcf = mr.util.genvcf:main',
            'kopass = mr.util.kopass:main',
            'things = mr.util.things:main',
            'networth = mr.networth.networth:main',
            'taxes = mr.networth.taxes:main',
            'utilities = mr.networth.utilities:main',
            'expenses = mr.networth.expenses:main',
            'mpw = mr.util.mpw:main',
            's = mr.util.inspector:main',
            'connect = mr.util.internet:connect',
            'disconnect = mr.util.internet:disconnect',
            'localcert = mr.util.localcert:main',
            'unzip = mr.util.unzip:main',
            'hostconf = mr.util.hostconf:main',
            'spameater = mr.spameater:local_main',
            'packmgr = mr.packmgr.main:main',
            'ji = mr.packmgr.main:main',
            'chroot-enter = mr.util.chroot:main',
            'intel-bl = mr.util.intel_backlight:main',
            'fma = mr.util.freemusicarchive:main',
            'dotfiles = mr.util.dotfiles:main',
            'userinit = mr.util.userinit:main',
            'userdestroy = mr.util.userdestroy:main',
            'vids = mr.videos:main',
        ],
    },
    include_package_data=True,
)
