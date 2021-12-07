from setuptools import setup
exec(open('avdb/__version__.py').read())

setup(
    name='avdb',
    version=VERSION,
    description='AFS version tracking database',
    long_description=open('README.rst').read(),
    author='Michael Meffie',
    author_email='mmeffie@sinenomine.net',
    url='https://github.com/meffie/avdb',
    packages=['avdb'],
    install_requires=[
        'SQLAlchemy',
        'six',
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
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development',
    ],
)
