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

import os
from sqlalchemy import create_engine, Column, DateTime, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql import func
from pprint import pformat

engine = None
Base = declarative_base()
Session = sessionmaker()

def mysql_create_db(admin, password, dbuser, dbpasswd, dbhost, dbname):
    """Create the mysql database and user."""
    db = create_engine("mysql://{admin}:{password}@{dbhost}".format(**locals()))
    db.execute("CREATE DATABASE {dbname}".format(**locals()))
    db.execute("CREATE USER '{dbuser}'@'localhost' IDENTIFIED BY '{dbpasswd}'".format(**locals()))
    db.execute("CREATE USER '{dbuser}'@'%%' IDENTIFIED BY '{dbpasswd}'".format(**locals()))
    db.execute("GRANT ALL PRIVILEGES ON {dbname}.* TO '{dbuser}'@'localhost' WITH GRANT OPTION".format(**locals()))
    db.execute("FLUSH PRIVILEGES")

def init_db(url=None):
    global engine
    if engine is None:
        if url is None:
            url = 'sqlite:///{}'.format(os.path.expanduser('~/avdb.db'))
        engine = create_engine(url)
        Session.configure(bind=engine)
        Base.metadata.create_all(engine)

class Cell(Base):
    __tablename__ = 'cell'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    desc = Column(String(255), default='')
    added = Column(DateTime, default=func.now())
    hosts = relationship('Host', backref='cell')

    def __repr__(self):
        return "<Cell(" \
            "id={self.id}, " \
            "name='{self.name}', " \
            "desc='{self.desc}', " \
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
        return session.query(Cell)

class Host(Base):
    __tablename__ = 'host'
    id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, ForeignKey('cell.id'))
    name = Column(String(255))
    address = Column(String(255), unique=True)
    added = Column(DateTime, default=func.now())
    nodes = relationship('Node', backref='host')

    def __repr__(self):
        return "<Host(" \
            "id={self.id}, " \
            "cell_id={self.cell_id}, " \
            "name='{self.name}', " \
            "address='{self.address}', " \
            "added={self.added}, " \
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

    def cellname(self):
        return self.host.cell.name

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
    _version = Column('version', String(255))
    added = Column(DateTime, default=func.now())

    @property
    def version(self):
        return pformat(self._version).strip("'") # flatten to ascii

    @version.setter
    def version(self, version):
        self._version = version

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
