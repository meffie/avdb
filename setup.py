from setuptools import setup
execfile('avdb/__version__.py')

setup(
    name='avdb',
    version=VERSION,
    description='AFS Version Database',
    author='Michael Meffie',
    author_email='mmeffie@sinenomine.net',
    url='https://www.sinenomine.net/',
    packages=['avdb'],
    install_requires=[
        'SQLAlchemy',
        'sh',
        'mpipe',
    ],
    entry_points={
        'console_scripts': [
            'avdb = avdb.__main__:main'
        ]
    },
)
