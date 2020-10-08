from setuptools import setup

setup(
    name='addons',
    version=1,
    packages=['addons'],
    entry_points={
        'console_scripts': [
            'compress-music = addons.util.compress_music:compress',
            'gen = addons.util.gen:gen',
            'github-2fa = addons.util.github:genpass',
            'srcfetcher = addons.srcfetcher:main',
            'take-screenshot = addons.util.screenshot:main',
            'hckrnews = addons.hckrnews.hckrnews:main',
            'relmon = addons.relmon:main',
            'updater = addons.updater.updater:main',
            'valet = addons.valet:main',
            'schedule = addons.util.schedule:main',
            'timers = addons.timers:main',
            'fetch-videos = addons.youtube:fetch_videos',
        ],
    },
    include_package_data=True,
)
