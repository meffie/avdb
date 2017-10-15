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
    active = Column(Integer, default=1)
    added = Column(DateTime, default=func.now())

    def __repr__(self):
        return "<Cell(id=%d, name='%s', active=%d, added='%s')>" % \
               (self.id, self.name, self.active, self.added)

    @staticmethod
    def add(session, name=name):
        cell = session.query(Cell).filter_by(name=name).first()
        if cell is None:
            cell = Cell(name=name)
            session.add(cell)
        return cell

    @staticmethod
    def list(session):
        return session.query(Cell).filter_by(active=1).all()

class Node(Base):
    __tablename__ = 'node'
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
        return "<Node(id=%d, cell_id=%d, name='%s', address='%s', active=%d, added='%s', checked='%s', replied='%s')>" \
               % (self.id, self.cell_id, self.name, self.address, self.active, self.added, self.checked, self.replied)

    @staticmethod
    def add(session, cell, name='', address=None, **kwargs):
        node = session.query(Node).filter_by(address=address).first()
        if node is None:
            node = Node(cell=cell, address=address, name=name, **kwargs)
            session.add(node)
        return node

    @staticmethod
    def list(session):
        return session.query(Node,Cell) \
                .filter(Node.cell_id == Cell.id) \
                .all()

class Service(Base):
    __tablename__ = 'service'
    __table_args__ = (UniqueConstraint('name', 'node_id'),)
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey('node.id'))
    node = relationship(Node)
    name = Column(String(255))
    version = Column(String(255))
    active = Column(Integer, default=1)
    added = Column(DateTime, default=func.now())
    checked = Column(DateTime)
    replied = Column(DateTime)
    changed = Column(DateTime)

    def __repr__(self):
        return "<Service(id=%d, node_id=%d, name='%s', version='%s', active=%d, checked='%s', replied='%s', changed='%s')>" \
                % (self.id, self.node_id, self.name, self.version, self.active, self.checked, self.replied, self.changed)

    @staticmethod
    def add(session, node, name='', **kwargs):
        service = session.query(Service).filter_by(node=node, name=name).first()
        if service is None:
            service = Service(node=node, name=name, **kwargs)
            session.add(service)
        return service

    @staticmethod
    def list(session):
        return session.query(Service, Node, Cell) \
                .filter(Service.id == 1) \
                .filter(Service.node_id == Node.id) \
                .filter(Node.cell_id == Cell.id) \
                .all()

def example():
    from pprint import pprint
    cellname = 'example.edu'
    session = Session()
    cell = Cell.add(session, name=cellname)
    node = Node.add(session, cell, name='afsdb1', address='1.2.3.4')
    Service.add(session, node, name='ptserver')
    Service.add(session, node, name='vlserver')
    Service.add(session, node, name='foobar', active=0)
    session.commit()
    print "cells"; pprint(session.query(Cell).all())
    print "nodes"; pprint(session.query(Node).all())
    print "services"; pprint(session.query(Service).all())
    print "active cells"; print Cell.list(session)
    print "active nodes"; print Node.list(session)
    print "active services"
    for s in Service.list(session):
        print s

if __name__ == "__main__":
    init_db()
    example()

