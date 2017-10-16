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

from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, create_engine
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
    desc = Column(String(255))
    active = Column(Integer, default=1)
    added = Column(DateTime, default=func.now())

    def __repr__(self):
        return "<Cell(id=%d, name='%s', active=%d, added='%s')>" % \
               (self.id, self.name, self.active, self.added)

    @staticmethod
    def add(session, name, addresses):
        cell = session.query(Cell).filter_by(name=name).first()
        if cell is None:
            cell = Cell(name=name)
            session.add(cell)
        for address in addresses:
            Host.add(session, cell, address)
        return cell

    @staticmethod
    def list(session):
        return session.query(Cell).filter_by(active=1).all()

class Host(Base):
    __tablename__ = 'host'
    id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, ForeignKey('cell.id'))
    cell = relationship(Cell)
    name = Column(String(255))
    address = Column(String(255), unique=True)
    active = Column(Integer, default=1)
    added = Column(DateTime, default=func.now())
    checked = Column(DateTime)
    replied = Column(DateTime)

    def __repr__(self):
        return "<Host(id=%d, cell_id=%d, name='%s', address='%s', " \
               "active=%d, added='%s', checked='%s', replied='%s')>" \
               % (self.id, self.cell_id, self.name, self.address,
                  self.active, self.added, self.checked, self.replied)

    @staticmethod
    def add(session, cell, address, name='', **kwargs):
        host = session.query(Host).filter_by(address=address).first()
        if host is None:
            host = Host(cell=cell, address=address, name=name, **kwargs)
            session.add(host)
        return host

    @staticmethod
    def list(session):
        return session.query(Cell, Host) \
                .filter(Cell.active == 1) \
                .filter(Cell.id == Host.cell_id) \
                .all()

class Node(Base):
    __tablename__ = 'node'
    __table_args__ = (UniqueConstraint('name', 'host_id'),)
    id = Column(Integer, primary_key=True)
    host_id = Column(Integer, ForeignKey('host.id'))
    host = relationship(Host)
    name = Column(String(255))
    active = Column(Integer, default=1)
    added = Column(DateTime, default=func.now())

    def __repr__(self):
        return "<Node(id=%d, host_id=%d, name='%s', active=%d, added='%s')>" \
                % (self.id, self.host_id, self.name, self.active, self.added)

    @staticmethod
    def add(session, host, name, **kwargs):
        node = session.query(Node).filter_by(host=host, name=name).first()
        if node is None:
            node = Node(host=host, name=name, **kwargs)
            session.add(node)
        return node

    @staticmethod
    def list(session):
        return session.query(Cell, Host, Node) \
                .filter(Cell.active == 1) \
                .filter(Cell.id == Host.cell_id) \
                .filter(Host.id == Node.host_id) \
                .all()

class Version(Base):
    __tablename__ = 'version'
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey('node.id'))
    node = relationship(Node)
    version = Column(String(255))
    added = Column(DateTime, default=func.now())

    def __repr__(self):
        return "<Version(id=%d, node_id=%d, version='%s', added='%s')>" \
                % (self.id, self.node_id, self.version, self.added)

    @staticmethod
    def add(session, node, version_string, **kwargs):
        version = session.query(Version).filter_by(node=node, version=version_string).first()
        if version is None:
            version = Version(node=node, version=version_string, **kwargs)
            session.add(version)
        return version

    @staticmethod
    def list(session):
        return session.query(Cell, Host, Node, Version) \
                .filter(Cell.active == 1) \
                .filter(Cell.id == Host.cell_id) \
                .filter(Host.id == Node.host_id) \
                .filter(Node.id == Version.node_id) \
                .all()
'''
def example():
    from pprint import pprint
    cellname = 'example.edu'
    session = Session()
    cell = Cell.add(session, name=cellname)
    host = Host.add(session, cell, name='afsdb1', address='1.2.3.4')
    node0 = Node.add(session, host, name='ptserver')
    node1 = Node.add(session, host, name='vlserver')
    node2 = Node.add(session, host, name='foobar', active=0)
    v0 = Version.add(session, node0, "1.0.0")
    v1 = Version.add(session, node0, "1.0.1")
    session.commit()
    print "cells"; pprint(session.query(Cell).all())
    print "hosts"; pprint(session.query(Host).all())
    print "nodes"; pprint(session.query(Node).all())
    print "active cells"; print Cell.list(session)
    print "active hosts"; print Host.list(session)
    print "active nodes"
    for s in Node.list(session):
        pprint(s)
    print "versions"
    for v in Version.list(session):
        pprint(v)

if __name__ == "__main__":
    init_db()
    example()
'''

