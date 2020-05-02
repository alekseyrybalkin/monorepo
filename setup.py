from setuptools import setup

setup(
    name='addons',
    version=__import__('addons').__version__,
    packages=['addons'],
    scripts=[
        'gen',
        'github-2fa',
        'srcfetcher',
        'take-screenshot',
    ],
    entry_points={
        'console_scripts': [
            'compress-music = addons.audio:compress',
            'fetch-videos = addons.youtube:fetch_videos',
            #'gen',
            #'github-2fa',
            #'srcfetcher',
            #'take-screenshot',
        ],
    },
    include_package_data=True,
)
