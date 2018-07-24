from setuptools import setup
exec(open('avdb/__version__.py').read())

setup(
    name='avdb',
    version=VERSION,
    description='AFS version tracking database',
    long_description=open('README.rst').read(),
    author='Michael Meffie',
    author_email='mmeffie@sinenomine.net',
    url='https://www.sinenomine.net/',
    packages=['avdb'],
    install_requires=[
        'SQLAlchemy',
        'sh',
        'mpipe',
        'pystache',
        'dnspython',
    ],
    entry_points={
        'console_scripts': [
            'avdb = avdb.__main__:main'
        ]
    },
)
