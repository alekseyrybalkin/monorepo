from setuptools import setup

setup(
    name='addons',
    version=__import__('addons').__version__,
    packages=['addons'],
    entry_points={
        'console_scripts': [
            'compress-music = addons.audio:compress',
            'fetch-videos = addons.youtube:fetch_videos',
            'gen = addons.gen:gen',
            'github-2fa = addons.github:genpass',
            'srcfetcher = addons.srcfetcher:main',
            'take-screenshot = addons.screenshot:main',
            'hckrnews = addons.hckrnews:main',
            'relmon = addons.relmon:main',
            'updater = addons.updater.updater:main',
        ],
    },
    include_package_data=True,
)
