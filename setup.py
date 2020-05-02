from setuptools import setup

setup(
    name='addons',
    version=__import__('addons').__version__,
    packages=['addons'],
    scripts=[
        'compress-music',
        'fetch-videos',
        'gen',
        'github-2fa',
        'srcfetcher',
        'take-screenshot',
    ],
    include_package_data=True,
)
