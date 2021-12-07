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
import os, sys, datetime, re, logging, mpipe, pystache, avdb
from sh import rxdebug
from avdb.subcmd import subcommand, argument, usage, dispatch, config
from avdb.model import mysql_create_db, init_db, Session, Cell, Host, Node, Version
from avdb.csdb import readfile, parse, lookup
from avdb.templates import template

log = logging.getLogger('avdb')

@subcommand()
def help_(**kwargs):
    """Display help message"""
    usage("""avdb [command] [options]

Scan public AFS servers for version information
and generate reports.
""")
    return 0

@subcommand()
def version_(**kwargs):
    """Print the version number and exit"""
    print(avdb.__version__)
    return 0

@subcommand(
    argument('--admin', default='root', help="database admin username"),
    argument('--password', help="database admin password"),
)
def init_(url=None, admin='root', password=None, **kwargs):
    """Create database tables"""
    if url is None:
        return 1
    # Create the database and tables.
    if url.startswith('sqlite://'):
        pass
    elif url.startswith('mysql://'):
        if password is None:
            log.error("mysql admin password is required to create database")
            return 2
        m = re.match(r'mysql://([^:]*):([^@]*)@([^/]*)/(.*)', url)
        if m is None:
            log.error("Unable to parse url '%s'", url)
            return 3
        dbuser,dbpasswd,dbhost,dbname = m.groups()
        log.info("Creating mysql database '%s' and user '%s'", dbname, dbuser)
        mysql_create_db(admin, password, dbuser, dbpasswd, dbhost, dbname)
    else:
        log.error("Unsupported db type in url '%s'", url)
        return 4
    log.info("Creating database tables")
    init_db(url)
    # Save our url in the ini file, if not already there.
    if not config.has_option('global', 'url') or config.get('global', 'url') != url:
        if not config.has_section('global'):
            config.add_section('global')
        config.set('global', 'url', url)
        inifile = os.path.expanduser('~/.avdb.ini')
        log.info("Saving database connection url in file '%s'", inifile)
        with open(inifile, 'w') as f:
            config.write(f)
    return 0

@subcommand(
    argument('cell', help="cellname"),
    argument('--desc', help="description"))
def add_(cell=None, desc=None, url=None, **kwargs):
    """Add a cell name to be scanned."""
    if cell is None:
        log.error("Missing cell argument")
        return 1
    init_db(url)
    session = Session()
    if cell == 'dynroot':
        log.warning("Ignoring dynroot cell name")
    else:
        Cell.add(session, name=cell, desc=desc)
    session.commit()
    return 0

@subcommand(
    argument('csdb', nargs='+', help="url or path to CellServDB file"))
def import_(csdb=None, name=None, url=None, **kwargs):
    """Import cells from CellServDB files"""
    if csdb is None:
        csdb = ()
    elif type(csdb) is not list and type(csdb) is not tuple:
        csdb = (csdb,)

    init_db(url)
    session = Session()

    text = []
    for path in csdb:
        text.append(readfile(path))
    cells = parse("".join(text))

    for cellname,cellinfo in cells.items():
        if cellname == 'dynroot':
            continue  # skip the synthetic cellname
        cell = Cell.add(session, name=cellname, desc=cellinfo['desc'])
        for address,hostname in cellinfo['hosts']:
            log.info("importing cell %s host %s (%s) from csdb", cellname, hostname, address)
            host = Host.add(session, cell=cell, address=address, name=hostname)
            Node.add(session, host, name='ptserver', port=7002)
            Node.add(session, host, name='vlserver', port=7003)
    session.commit()
    return 0

@subcommand(
    argument('--all', action='store_true', help="activate all cells"),
    argument('--cell', help="cell name"))
def activate_(all=False, cell='', url=None, **kwargs):
    """Set activation status"""
    init_db(url)
    session = Session()
    count = 0
    if not (all or cell):
        log.error("Specify --all or --cell")
        return 1
    query = session.query(Node).filter_by(active=False)
    for node in query:
        if all or node.cellname() == cell:
            node.active = True
            count += 1
    session.commit()
    log.info("activated {count} items".format(count=count))
    return 0

@subcommand(
    argument('--cell', required=True, help="cell name"))
def deactivate_(cell='', url=None, **kwargs):
    """Clear activation status"""
    init_db(url)
    session = Session()
    count = 0
    query = session.query(Node).filter_by(active=True)
    for node in query:
        if node.cellname() == cell:
            node.active = False
            count += 1
    session.commit()
    log.warn("deactivated {count} items".format(count=count))
    return 0

@subcommand()
def list_(url=None, **kwargs):
    """List cells"""
    init_db(url)
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
def scan_(nprocs=10, url=None, **kwargs):
    """Scan for versions"""
    init_db(url)
    session = Session()

    def lookup_cell(cellname):
        cellinfo = lookup(cellname)
        return (cellname, cellinfo)

    def get_version(value):
        """Get the version string from the remote host."""
        node_id,address,port = value
        version = None
        prefix = "AFS version:"
        try:
            for line in rxdebug(address, port, '-version'):
                if line.startswith(prefix):
                    version = line.replace(prefix,'').strip()
        except:
            version = None
        return (node_id, version)

    stage = mpipe.UnorderedStage(lookup_cell, nprocs)
    pipe = mpipe.Pipeline(stage)
    for cell in Cell.cells(session):
        log.info("looking up hosts for cell %s", cell.name)
        pipe.put(cell.name)
    pipe.put(None)

    for result in pipe.results():
        cellname,cellinfo = result
        cell = Cell.add(session, name=cellname)
        for address,hostname in cellinfo:
            log.info("importing cell %s host %s (%s) from dns", cellname, hostname, address)
            host = Host.add(session, cell=cell, address=address, name=hostname)
            Node.add(session, host, name='ptserver', port=7002)
            Node.add(session, host, name='vlserver', port=7003)
    session.commit()

    stage = mpipe.UnorderedStage(get_version, nprocs)
    pipe = mpipe.Pipeline(stage)

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
def report_(format='csv', output=None, url=None, **kwargs):
    """Generate version report"""
    init_db(url)
    session = Session()
    query = session.query(Cell, Host, Node, Version).\
        filter(Cell.id == Host.cell_id).\
        filter(Host.id == Node.host_id).\
        filter(Node.id == Version.node_id).\
        order_by(Cell.name, Host.address)
    results = []
    for cell,host,node,version in query:
        results.append({'cell':cell, 'host':host, 'node':node, 'version':version})
    generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    context = {'generated':generated, 'results':results}
    renderer = pystache.Renderer()
    if output:
        with open(output, 'w') as out:
            out.write(renderer.render(template[format], context))
    else:
        sys.stdout.write(renderer.render(template[format], context))
    return 0

def main():
    return dispatch()

if __name__ == '__main__':
    sys.exit(main())
