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

import sys, logging, mpipe, sh
from avdb.subcmd import subcommand, argument, usage, dispatch
from avdb.model import init_db, Session, Cell, Host, Node, Version
from avdb.csdb import readfile, parse

log = logging.getLogger('avdb')

@subcommand()
def help(args):
    """Display help message"""
    usage("""avdb [command] [options]

Scan public AFS servers for version information
and generate reports.
""")
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
    argument('csdb', nargs='+', help="url or path to CellServDB file"))
def import__(args): # Trailing underscores to avoid reserved name 'import'.
    """Import cells from CellServDB files"""
    init_db()
    session = Session()
    text = []
    for path in args.csdb:
        text.append(readfile(path))
    cells = parse("".join(text))
    for cellname,cellinfo in cells.items():
        cell = Cell.add(session, name=cellname, desc=cellinfo['desc'])
        for address,hostname in cellinfo['hosts']:
            host = Host.add(session, cell=cell, address=address, name=hostname)
            Node.add(session, host, name='ptserver', port=7002)
            Node.add(session, host, name='vlserver', port=7003)
    session.commit()
    return 0

@subcommand(
    argument('cell', help="cell name"),
    argument('-s', '--status', choices=['active', 'inactive'], help="set activation status"))
def change(args):
    """Change cell status"""
    init_db()
    session = Session()
    cell = session.query(Cell).filter(Cell.name == args.cell).first()
    if cell is None:
        log.error("cell {args.cell} not found.".format(args=args))
        return 2
    if args.status == 'active':
        cell.active = True
    elif args.status == 'inactive':
        cell.active = False
    session.commit()
    return 0

@subcommand(
    argument("--all", action="store_true", help="list inactive cells too"))
def list(args):
    """List cells"""
    init_db()
    session = Session()
    for cell in Cell.cells(session, all=args.all):
        print "name:{cell.name} desc:'{cell.desc}' active:{cell.active}".format(cell=cell)
        for host in cell.hosts:
            print "\thost:{host.name} address:{host.address} active:{host.active}".format(host=host)
            for node in host.nodes:
                print "\t\tnode:{node.name} port:{node.port} active:{node.active}".format(node=node)
    return 0

@subcommand(
    argument('--nprocs', type=int, default=10, help="number of processes"))
def scan(args):
    """Scan for versions"""
    try:
        rxdebug = sh.Command('rxdebug')
    except sh.CommandNotFound:
        log.error("Unable to find rxdebug")
        return 1

    def get_version(value):
        """Get the version string from the remote host."""
        node_id,address,port = value
        version = None
        prefix = "AFS version:"
        try:
            output = rxdebug(address, port, '-version')
            for line in output.stdout.splitlines():
                if line.startswith(prefix):
                    version = line.replace(prefix, "").strip()
        except:
            log.warn("Unable to reach endpoint %s:%d", address, port)
        return (node_id, version)

    stage = mpipe.UnorderedStage(get_version, args.nprocs)
    pipe = mpipe.Pipeline(stage)

    init_db()
    session = Session()
    for node in session.query(Node):
        if node.active and node.host.active and node.host.cell.active:
            log.info("scanning node {node.host.address}:{node.port} "\
                     "in {node.host.cell.name}".format(node=node))
            pipe.put((node.id, node.host.address, node.port))
        else:
            log.info("skipping inactive node {node.host.address}:{node.port} "\
                     "in {node.host.cell.name}".format(node=node))
    pipe.put(None)

    for result in pipe.results():
        node_id,version = result
        node = session.query(Node).filter_by(id=node_id).one()
        if version:
            log.info("got version from {node.host.address}:{node.port}: {version}" \
                    .format(node=node, version=version))
            Version.add(session, node=node, version=version)
        else:
            log.info("could not get version from {node.host.address}:{node.port}" \
                    .format(node=node))
            node.active = 0
    session.commit()
    return 0

@subcommand()
def report(args):
    """Generate version report"""
    init_db()
    session = Session()
    query = session.query(Cell,Host,Node,Version) \
                .join(Host) \
                .join(Node) \
                .join(Version) \
                .order_by(Cell.name, Host.address)
    for cell,host,node,version in query:
        print cell.name, host.address, node.name, version.version
    return 0

def main():
    return dispatch()

if __name__ == '__main__':
    sys.exit(main())
