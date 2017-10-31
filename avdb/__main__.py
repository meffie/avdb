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

from __future__ import print_function
import sys, os, datetime, logging, mpipe, sh, pystache
from avdb.subcmd import subcommand, argument, usage, dispatch
from avdb.model import init_db, Session, Cell, Host, Node, Version
from avdb.csdb import readfile, parse, lookup
from avdb.templates import template

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
    print(__version__)
    return 0

@subcommand()
def init(args):
    """Create database tables"""
    init_db()
    return 0

@subcommand(
    argument('--csdb', nargs='+', default=[], help="url or path to CellServDB file"),
    argument('--name', nargs='+', default=[], help="cellname for dns lookup"))
def import__(args): # Trailing underscores to avoid reserved name 'import'.
    """Import cells from CellServDB files"""
    init_db()
    session = Session()
    if args.csdb:
        text = []
        for path in args.csdb:
            text.append(readfile(path))
        cells = parse("".join(text))
        for cellname,cellinfo in cells.items():
            cell = Cell.add(session, name=cellname, desc=cellinfo['desc'])
            for address,hostname in cellinfo['hosts']:
                log.info("importing cell %s host %s (%s) from csdb", cellname, hostname, address)
                host = Host.add(session, cell=cell, address=address, name=hostname)
                Node.add(session, host, name='ptserver', port=7002)
                Node.add(session, host, name='vlserver', port=7003)
            for address,hostname in lookup(cellname):
                log.info("importing cell %s host %s (%s) from dns", cellname, hostname, address)
                host = Host.add(session, cell=cell, address=address, name=hostname)
                Node.add(session, host, name='ptserver', port=7002)
                Node.add(session, host, name='vlserver', port=7003)
    if args.name:
        for cellname in args.name:
            cell = Cell.add(session, name=cellname)
            for address,hostname in lookup(cellname):
                log.info("importing cell %s host %s (%s) from dns", cellname, hostname, address)
                host = Host.add(session, cell=cell, address=address, name=hostname)
                Node.add(session, host, name='ptserver', port=7002)
                Node.add(session, host, name='vlserver', port=7003)
    session.commit()
    return 0

@subcommand(
    argument('--all', action='store_true', help="activate all cells"),
    argument('--cell', help="cell name"))
def activate(args):
    """Set activation status"""
    init_db()
    session = Session()
    count = 0
    if not (args.all or args.cell):
        log.error("Specify --all or --cell")
        return 1
    query = session.query(Node).filter_by(active=False)
    for node in query:
        if args.all or node.cellname() == args.cell:
            node.active = True
            count += 1
    session.commit()
    log.info("activated {count} items".format(count=count))
    return 0

@subcommand(
    argument('--cell', required=True, help="cell name"))
def deactivate(args):
    """Clear activation status"""
    init_db()
    session = Session()
    count = 0
    query = session.query(Node).filter_by(active=True)
    for node in query:
        if node.cellname() == args.cell:
            node.active = False
            count += 1
    session.commit()
    log.warn("deactivated {count} items".format(count=count))
    return 0

@subcommand()
def list(args):
    """List cells"""
    init_db()
    session = Session()
    for cell in Cell.cells(session):
        print("name:{cell.name} desc:'{cell.desc}'".format(cell=cell))
        for host in cell.hosts:
            print("\thost:{host.name} address:{host.address}".format(host=host))
            for node in host.nodes:
                print("\t\tnode:{node.name} port:{node.port} active:{node.active}".format(node=node))
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
            for line in rxdebug(address, port, '-version'):
                if line.startswith(prefix):
                    version = line.strip(prefix).strip()
        except:
            version = None
        return (node_id, version)

    stage = mpipe.UnorderedStage(get_version, args.nprocs)
    pipe = mpipe.Pipeline(stage)

    init_db()
    session = Session()
    for node in session.query(Node):
        if node.active:
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
            if not node.active:
                node.active = True
        else:
            log.warning("could not get version from {node.host.address}:{node.port}" \
                    .format(node=node))
            if node.active:
                log.info("deactivating node {node.host.address}:{node.port}" \
                    .format(node=node))
                node.active = False
    session.commit()
    return 0

@subcommand(
    argument('-f', '--format', choices=['csv', 'html'], default='csv', help="output format"),
    argument('-o', '--output', help="output file"))
def report(args):
    """Generate version report"""
    init_db()
    session = Session()
    query = session.query(Cell,Host,Node,Version) \
                .join(Host) \
                .join(Node) \
                .join(Version) \
                .order_by(Cell.name, Host.address)
    results = []
    for cell,host,node,version in query:
        results.append({
            'cell':cell.name,
            'host':host.address,
            'node':node.name,
            'version':version.version,
            })
    generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    context = {'generated':generated, 'results':results}
    renderer = pystache.Renderer()
    if args.output:
        out = open(args.output, 'w')
    else:
        out = sys.stdout
    out.write(renderer.render(template[args.format], context))
    out.close()
    return 0

def main():
    return dispatch()

if __name__ == '__main__':
    sys.exit(main())
