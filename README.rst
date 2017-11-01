avdb - afs version tracking database
====================================

avdb is a tool to run rxdebug in batches to find versions of AFS servers
running in the wild.  The data is stored in a small database. sqlite is
used by default.

Installation
============

Install the OpenAFS rxdebug command. This may be installed from packages or
from building from source. Currently rxdebug is the only OpenAFS program used
by avdb. A cache manager is not required.

Install avdb with the provided makefile.::

    $ sudo make install    # global install

or::

    $ make install-user    # --user install

Create the database tables with the init commmand.
The sqlite db file will be created in the file ~/avdb.db::

    $ avdb init

Usage
=====

Import the list of cells to be scanned.::

    $ avdb import \
       https://grand.central.org/dl/cellservdb/CellServDB \
       http://download.sinenomine.net/service/afs3/CellServDB

    $ avdb list

Scan the hosts with the scan command.::

    $ avdb scan --nprocs 100 --verbose

List the versions with the report command.::

    $ avdb report

Configuration
=============

avdb command line option defaults can be set by an ini style configuration
file. The site-wide configuation file is /etc/avdb.ini. The per-user
configuration file is located at $HOME/.avdb.ini.  The per-user configuration
file will override options present in the site-wide file, and command-line
arguments will override the configuration.

The configuration file contains a global section for common options, which
include the sql url to specify the database connection, and common logging
options.  Each subcommand has a separate section for specifying defaults
for the supcommand.

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

Python scripting
================

In addition to the command line interface, the avdb module may be imported into
Python programs and the subcommands may be invoked directly as regular Python
functions. The subcommand functions have a single trailing underscore, to avoid
naming conflicts with standard python names, e.g., the function for the import
subcommand is called import_.

Example::

    import avdb
    avdb.init_('sqlite:////tmp/example.db')
    avdb.import_(name='sinenomine.net')
    avdb.scan_(nprocs=20)
    avdb.report_(format='html', output='myfile.html')

