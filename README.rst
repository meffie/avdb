avdb - afs version tracking database
====================================

avdb is a tool to run rxdebug in batches to find versions of AFS servers
running in the wild.  The data is stored in a small sql database. sqlite is
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

