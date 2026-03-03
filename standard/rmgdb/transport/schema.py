from sqlalchemy import (
    Column,
    Integer,
    String,
    event,
    SmallInteger,
    Float,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column

from rmgdb.transport.triggers import (
    check_short_desc,
    delete_empty_desc,
)

SCHEMA_BASE = declarative_base()

# Transport libraries table
class TransportLibraries(SCHEMA_BASE):
    __tablename__ = "transport_libraries_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    molecule = Column(String)
    shape_index = Column(Integer)
    epsilon = Column(Float)
    epsilon_unit = Column(String)
    sigma = Column(Float)
    sigma_unit = Column(String)
    dipole_moment = Column(Float)
    dipole_moment_unit = Column(String)
    polarizability = Column(Float)
    polarizability_unit = Column(String)
    rotrelaxcollnum = Column(Float)

# Transport groups table
class TransportGroups(SCHEMA_BASE):
    __tablename__ = "transport_groups_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    group = Column(String)
    tc = Column(Float)
    pc = Column(Float)
    vc = Column(Float)
    tb = Column(Float)
    structure_index = Column(Integer)

# Group tree table
class TransportGroupsTree(SCHEMA_BASE):
    __tablename__ = "transport_groups_tree_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("transport_groups_table.id"))
    child_id = mapped_column(ForeignKey("transport_groups_table.id"))

# Triggers
event.listen(TransportLibraries, "before_insert", check_short_desc)
event.listen(TransportLibraries, "before_insert", delete_empty_desc)

event.listen(TransportGroups, "before_insert", check_short_desc)
event.listen(TransportGroups, "before_insert", delete_empty_desc)
