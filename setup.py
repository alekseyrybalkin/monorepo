from setuptools import setup

setup(
    name='addons',
    version=__import__('addons').__version__,
    packages=['addons'],
    scripts=[
        'networth',
        'exercise',
        'things',
        'kopass',
        'srcfetcher',
        'compress-music',
    ],
    include_package_data=True,
)
