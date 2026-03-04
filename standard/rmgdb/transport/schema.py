from sqlalchemy import (
    Column,
    Integer,
    String,
    event,
    ForeignKey,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column

# Assuming the existing triggers are reusable and placed in a common place, 
# or we can import them from statmech/triggers for now.
from rmgdb.statmech.triggers import (
    check_short_desc,
    delete_empty_desc,
)

SCHEMA_BASE = declarative_base()

# ---------------------------------------------------------------------
# Groups and associated tables
# ---------------------------------------------------------------------
class Groups(SCHEMA_BASE):
    __tablename__ = "groups_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    group = Column(String)

event.listen(Groups, "before_insert", check_short_desc)
event.listen(Groups, "before_insert", delete_empty_desc)


class GroupsTree(SCHEMA_BASE):
    __tablename__ = "groups_tree_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("groups_table.id"))
    child_id = mapped_column(ForeignKey("groups_table.id"))


class CriticalPointGroupContribution(SCHEMA_BASE):
    __tablename__ = "critical_point_group_contribution_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("groups_table.id"))
    Tc = Column(Float)
    Pc = Column(Float)
    Vc = Column(Float)
    Tb = Column(Float)
    structureIndex = Column(Integer)


# ---------------------------------------------------------------------
# Libraries and associated tables
# ---------------------------------------------------------------------
class TransportLibraries(SCHEMA_BASE):
    __tablename__ = "transport_libraries_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    adjacency_list = Column(String)

event.listen(TransportLibraries, "before_insert", check_short_desc)
event.listen(TransportLibraries, "before_insert", delete_empty_desc)


class TransportData(SCHEMA_BASE):
    __tablename__ = "transport_data_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("transport_libraries_table.id"))
    
    shapeIndex = Column(Integer)
    epsilon = Column(Float)
    epsilon_unit = Column(String)
    sigma = Column(Float)
    sigma_unit = Column(String)
    dipoleMoment = Column(Float)
    dipoleMoment_unit = Column(String)
    polarizability = Column(Float)
    polarizability_unit = Column(String)
    rotrelaxcollnum = Column(Float)
