from sqlalchemy import Column, Integer, String, Float, ForeignKey, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column
from rmgdb.statmech.triggers import check_short_desc, delete_empty_desc

SCHEMA_BASE = declarative_base()

class Groups(SCHEMA_BASE):
    __tablename__ = "groups_table"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    group = Column(String)
    solute_pointer = Column(String)

class GroupsTree(SCHEMA_BASE):
    __tablename__ = "groups_tree_table"
    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("groups_table.id"))
    child_id = mapped_column(ForeignKey("groups_table.id"))

class SoluteLibraries(SCHEMA_BASE):
    __tablename__ = "solute_libraries_table"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    molecule = Column(String)

class SolventLibraries(SCHEMA_BASE):
    __tablename__ = "solvent_libraries_table"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    molecule = Column(String)

class SoluteData(SCHEMA_BASE):
    __tablename__ = "solute_data_table"
    id = Column(Integer, primary_key=True)
    solute_library_parent_id = mapped_column(ForeignKey("solute_libraries_table.id"))
    group_parent_id = mapped_column(ForeignKey("groups_table.id"))
    S = Column(Float); B = Column(Float); E = Column(Float)
    L = Column(Float); A = Column(Float); V = Column(Float)

class DataCountGAV(SCHEMA_BASE):
    __tablename__ = "data_count_gav_table"
    id = Column(Integer, primary_key=True)
    group_parent_id = mapped_column(ForeignKey("groups_table.id"))
    S = Column(Integer); B = Column(Integer); E = Column(Integer)
    L = Column(Integer); A = Column(Integer)
    
class SolventData(SCHEMA_BASE):
    __tablename__ = "solvent_data_table"
    id = Column(Integer, primary_key=True)
    solvent_library_parent_id = mapped_column(ForeignKey("solvent_libraries_table.id"))
    s_g = Column(Float); b_g = Column(Float); e_g = Column(Float); l_g = Column(Float); a_g = Column(Float); c_g = Column(Float)
    s_h = Column(Float); b_h = Column(Float); e_h = Column(Float); l_h = Column(Float); a_h = Column(Float); c_h = Column(Float)
    A = Column(Float); B = Column(Float); C = Column(Float); D = Column(Float); E = Column(Float)
    alpha = Column(Float); beta = Column(Float); eps = Column(Float); n = Column(Float); name_in_coolprop = Column(String)

class DataCountSolvent(SCHEMA_BASE):
    __tablename__ = "data_count_solvent_table"
    id = Column(Integer, primary_key=True)
    solvent_library_parent_id = mapped_column(ForeignKey("solvent_libraries_table.id"))
    dGsolvCount = Column(Integer); dGsolvMAE_val = Column(Float); dGsolvMAE_unit = Column(String)
    dHsolvCount = Column(Integer); dHsolvMAE_val = Column(Float); dHsolvMAE_unit = Column(String)

for table in [Groups, SoluteLibraries, SolventLibraries]:
    event.listen(table, "before_insert", check_short_desc)
    event.listen(table, "before_insert", delete_empty_desc)
