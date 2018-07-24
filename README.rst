avdb - AFS version tracking database
====================================

``avdb`` runs the OpenAFS ``rxdebug`` command in batches to find versions of
AFS servers running in the wild.  The data is stored in a small database.
Sqlite and mysql databases are currently supported.

Installation
============

Install the OpenAFS ``rxdebug`` command before installing ``avdb``.  The
``rxdebug`` command may be installed from packages or from building the OpenAFS
user-space packages from source. ``rxdebug`` is the only OpenAFS program used
by avdb at this time. A cache manager (OpenAFS client) is not required.

A makefile is provided with ``avdb`` to facilate development and installation
from a git checkout.  The avdb package can be installed directly from a git
checkout with the ``install-user`` target::

    $ make install-user

or for site-wide installation::

    $ sudo make install

Next, run the ``avdb init`` subcommand to create the database and tables.
Provide a connection url on the command line to specify the database type and
the connection credentials.  The connection url will be saved in the avdb
config file ``~/.avdb.ini`` for subsequent invocations of ``avdb``.

To create an sqlite database::

    $ avdb init --url sqlite:////<path>/<to>/avdb.db

To create a mysql database::

    $ avdb init --url mysql://<user>:<secret>@<hostname>/avdb \
                --admin <mysql-admin-user> \
                --password <mysql-admin-password>

Example usage
=============

Import the list of cells to be scanned with the 'import' subcommand.::

    $ avdb import --csdb https://grand.central.org/dl/cellservdb/CellServDB \
                  --name sinenomine.net

    $ avdb list

Periodically scan the hosts to find versions with the 'scan' subcommand.::

    $ avdb scan --nprocs 100 --verbose

Output the versions discovered the 'report' subcommand.::

    $ avdb report --output /tmp/results --format html

Configuration
=============

avdb command line option defaults may be set by an ini style configuration
file. The site-wide configuation file is ``/etc/avdb.ini``, and the per-user
configuration file is located at ``$HOME/.avdb.ini``.  The per-user
configuration file will override options present in the site-wide file, and
command-line arguments will override the values in the configuration files.

The configuration file contains a global section for common options, which
includes the sql url to specify the database connection and common logging
options. There is are separate sections for each avdb subsections to specify
default values for each subcommand.  See the command line help for option names.

Example configuration file::

    $ cat ~/.avdb.ini
    [global]
    url = sqlite:////var/lib/avdb/example.db
    log = /tmp/avdb.log
    
    [scan]
    nprocs = 10
    
    [report]
    format = html
    output = /var/www/html/avdb.html

Using avdb in Python
====================

In addition to the command line interface, the avdb module may be imported into
Python programs. This allows the avdb subcommands to be invoked directly as
regular Python functions. All of the subcommand functions have a single
trailing underscore to avoid naming conflicts with standard python names. For
example, function for the import subcommand is called ``import_``.

The database connection url must be set once before calling avdb subcommand
functions. Use the ``avdb.model.init_db()`` function to set the connection url.

The avdb config parser object, if needed, is available as
``avdb.subcmd.config``.

Example::

    import avdb
    url = avdb.subcmd.config.get('global', 'url')
    avdb.model.init_db(url)
    avdb.import_(name='sinenomine.net')
    avdb.scan_(nprocs=20)
    avdb.report_(format='html', output='myfile.html')

