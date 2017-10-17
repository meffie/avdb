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
#------------------------------------------------------------------------------

"""AFS version database model"""

from sqlalchemy import create_engine, Column, DateTime, String, Integer, ForeignKey, or_
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql import func

Base = declarative_base()
Session = sessionmaker()

def init_db():
    engine = create_engine('sqlite:////tmp/avdb.db')
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)

class Cell(Base):
    __tablename__ = 'cell'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    desc = Column(String(255), default='')
    active = Column(Integer, default=1)
    added = Column(DateTime, default=func.now())
    hosts = relationship('Host', backref='cell')

    def __repr__(self):
        return "<Cell(" \
            "id={self.id}, " \
            "name='{self.name}', " \
            "desc='{self.desc}', " \
            "active={self.active}, " \
            "added='{self.added}')>" \
            .format(self=self)

    @staticmethod
    def add(session, name, **kwargs):
        cell = session.query(Cell).filter_by(name=name).first()
        if cell is None:
            cell = Cell(name=name, **kwargs)
            session.add(cell)
        return cell

    @staticmethod
    def cells(session, all=False):
        return session.query(Cell) \
                .filter(or_(all, Cell.active == 1))

class Host(Base):
    __tablename__ = 'host'
    id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, ForeignKey('cell.id'))
    name = Column(String(255))
    address = Column(String(255), unique=True)
    active = Column(Integer, default=1)
    added = Column(DateTime, default=func.now())
    checked = Column(DateTime)
    replied = Column(DateTime)
    nodes = relationship('Node', backref='host')

    def __repr__(self):
        return "<Host(" \
            "id={self.id}, " \
            "cell_id={self.cell_id}, " \
            "name='{self.name}', " \
            "address='{self.address}', " \
            "active={self.active}, " \
            "added={self.added}, " \
            "checked={self.checked}, " \
            "replied={self.replied})>" \
            .format(self=self)

    @staticmethod
    def add(session, cell, address, name='', **kwargs):
        host = session.query(Host).filter_by(address=address).first()
        if host is None:
            host = Host(cell=cell, address=address, name=name, **kwargs)
            session.add(host)
        return host

class Node(Base):
    __tablename__ = 'node'
    __table_args__ = (UniqueConstraint('name', 'host_id'),)
    id = Column(Integer, primary_key=True)
    host_id = Column(Integer, ForeignKey('host.id'))
    name = Column(String(255))
    port = Column(Integer, default=0)
    active = Column(Integer, default=1)
    added = Column(DateTime, default=func.now())
    versions = relationship('Version', backref='node')

    def __repr__(self):
        return "<Node(" \
            "id={self.id}, " \
            "host_id={self.host_id}, " \
            "name='{self.name}', " \
            "active={self.active}, " \
            "added={self.added})>" \
            .format(self=self)

    @staticmethod
    def add(session, host, name, **kwargs):
        node = session.query(Node).filter_by(host=host, name=name).first()
        if node is None:
            node = Node(host=host, name=name, **kwargs)
            session.add(node)
        return node

class Version(Base):
    __tablename__ = 'version'
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey('node.id'))
    version = Column(String(255))
    added = Column(DateTime, default=func.now())

    def __repr__(self):
        return "<Version(" \
            "id={self.id}, " \
            "node_id={self.node_id}, " \
            "version='{self.version}', " \
            "added={self.added})>" \
            .format(self=self)

    @staticmethod
    def add(session, node, version, **kwargs):
        version_ = session.query(Version).filter_by(node=node, version=version).first()
        if version_ is None:
            version_ = Version(node=node, version=version, **kwargs)
            session.add(version_)
        return version_


# Example data model usage.
if __name__ == "__main__":
    from pprint import pprint
    init_db()
    session = Session()

    # example cell
    cell = Cell.add(session, name='example.edu', desc='example cell')
    for address in ('1.1.1.1', '2.2.2.2', '3.3.3.3'):
        host = Host.add(session, cell, address=address)
        for name,port in [('ptserver',7002), ('vlserver',7003)]:
            node = Node.add(session, host, name=name, port=port)
            for version in ('1.0.0', '1.1.0'):
                Version.add(session, node, version=version)
    host = Host.add(session, cell, address='0.0.0.0', name='old', active=0)
    Node.add(session, host, name='old')
    session.commit()

    # add an inactive cell
    cell = Cell.add(session, name='bogus.com', desc='inactive cell', active=0)
    host = Host.add(session, cell, address='255.255.255.255', name='deadbeef', active=0)
    Node.add(session, host, name='beefface')
    session.commit()

    print "dump tables:"
    pprint(Cell.cells(session, all=True).all()); print ""
    pprint(session.query(Host).all()); print ""
    pprint(session.query(Node).all()); print ""
    pprint(session.query(Version).all()); print ""

    print "list cells and hosts"
    for cell in Cell.cells(session, all=True):
        pprint([cell.name, cell.hosts])
    print ""

    print "add a version"
    cell,host,node = session.query(Cell,Host,Node) \
            .join(Host) \
            .join(Node) \
            .filter(Cell.name == 'example.edu') \
            .filter(Host.address == '2.2.2.2') \
            .filter(Node.name == 'ptserver') \
            .one()
    pprint([node,node.versions])
    Version.add(session, node=node, version='1.2.0')
    session.commit()
    print ""

    print "list nodes"
    for node in session.query(Node):
        if node.host.active and node.host.cell.active:
            print "node"
            pprint(node)
            pprint(node.host)
            pprint(node.host.cell)
            print ""
        else:
            print "inactive node"
            pprint(node)
            pprint(node.host)
            pprint(node.host.cell)
            print ""
