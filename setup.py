from setuptools import setup, find_packages

setup(
    name='addons',
    version=1,
    packages=find_packages(),
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
            'fetch-videos = addons.youtube:fetch_videos',
            'timers = addons.timers:main',
            'domains = addons.domains:main',
            'heaven-gentimers = addons.heaven.timers:main',
            'heaven-gendomains = addons.heaven.domains:main',
        ],
    },
    include_package_data=True,
)
