# Copyright (c) 2017 Sine Nomine Associates
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""AFS version database cli"""

import sys
import logging
import avdb.csdb
import avdb.rxdebug
from avdb.subcmd import subcommand, argument, summary, dispatch
from avdb.model import init_db, Session, Cell, Host, Node, Version

log = logging.getLogger(__name__)

@subcommand()
def help(args):
    """Display help message"""
    print """avdb [command] [options]

Scan public AFS servers for version information
and generate reports.
"""
    summary()
    return 0

@subcommand()
def version(args):
    """Print the version number and exit"""
    from avdb import __version__
    print __version__
    return 0

@subcommand()
def init(args):
    """Create database tables"""
    init_db()
    return 0

@subcommand(
    argument('cell', help="cell name"),
    argument('host', nargs="+", help="database address"))
def add(args):
    """Add a cell"""
    init_db()
    session = Session()
    cell = Cell.add(session, name=args.cell)
    for host in args.host:
        Host.add(session, cell, address=host)
    session.commit()
    return 0

@subcommand()
def edit(args):
    """Change cell info (not implemented)"""
    return 0

@subcommand(
    argument("--all", action="store_true", help="list inactive cells too"))
def list(args):
    """List cells"""
    from pprint import pprint
    init_db()
    session = Session()
    for cell in Cell.cells(session, all=args.all):
        pprint([cell, cell.hosts])
    return 0

@subcommand(
    argument('csdb', nargs='+', help="url or path to CellServDB file"))
def import__(args): # Trailing underscores to avoid reserved name 'import'.
    """Import cell info from CellServDB files"""
    init_db()
    session = Session()
    text = []
    for path in args.csdb:
        text.append(avdb.csdb.readfile(path))
    cells = avdb.csdb.parse("".join(text))
    for cellname,cellinfo in cells.items():
        cell = Cell.add(session, name=cellname, desc=cellinfo['desc'])
        for address,hostname in cellinfo['hosts']:
            host = Host.add(session, cell=cell, address=address, name=hostname)
            Node.add(session, host, name='ptserver', port=7002)
            Node.add(session, host, name='vlserver', port=7003)
    session.commit()
    return 0

@subcommand()
def scan(args):
    """Scan for versions (not implemented)"""
    from pprint import pprint
    init_db()
    session = Session()
    for node in session.query(Node):
        pprint(node)
        if node.host.active and node.host.cell.active:
            pprint(node.host)
            pprint(node.host.cell)
            log.info("scanning {node.host.address}:{node.port}".format(node=node))
            version_string = avdb.rxdebug.version(node.host.address, node.port)
            log.info("v = %s", version_string)
            if version_string:
                Version.add(session, node=node, version=version_string)
                session.commit()
    return 0

@subcommand()
def report(args):
    """Generate version report (not implemented)"""
    from pprint import pprint
    init_db()
    session = Session()
    for version in session.query(Version):
        pprint([version, version.node.host.cell])
    return 0

def main():
    logging.basicConfig(level=logging.INFO)
    log.info("in main")
    return dispatch()

if __name__ == '__main__':
    sys.exit(main())
