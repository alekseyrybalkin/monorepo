from setuptools import setup

setup(
    name='addons',
    version=1,
    packages=['addons'],
    entry_points={
        'console_scripts': [
            'compress-music = addons.audio:compress',
            'gen = addons.gen:gen',
            'github-2fa = addons.github:genpass',
            'srcfetcher = addons.srcfetcher:main',
            'take-screenshot = addons.screenshot:main',
            'hckrnews = addons.hckrnews.hckrnews:main',
            'relmon = addons.relmon:main',
            'updater = addons.updater.updater:main',
            'valet = addons.valet:main',
            'schedule = addons.schedule:main',
            'timers = addons.timers:main',
        ],
    },
    include_package_data=True,
)
