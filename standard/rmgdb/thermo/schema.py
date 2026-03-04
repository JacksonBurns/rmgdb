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

from rmgdb.statmech.triggers import (
    check_short_desc,
    delete_empty_desc,
)

SCHEMA_BASE = declarative_base()


class Groups(SCHEMA_BASE):
    __tablename__ = "groups_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    group = Column(String)
    thermo_pointer = Column(String)

event.listen(Groups, "before_insert", check_short_desc)
event.listen(Groups, "before_insert", delete_empty_desc)

class GroupsTree(SCHEMA_BASE):
    __tablename__ = "groups_tree_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("groups_table.id"))
    child_id = mapped_column(ForeignKey("groups_table.id"))

class ThermoLibraries(SCHEMA_BASE):
    __tablename__ = "thermo_libraries_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    adjacency_list = Column(String)

event.listen(ThermoLibraries, "before_insert", check_short_desc)
event.listen(ThermoLibraries, "before_insert", delete_empty_desc)

class ThermoDepositories(SCHEMA_BASE):
    __tablename__ = "thermo_depositories_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    adjacency_list = Column(String)

event.listen(ThermoDepositories, "before_insert", check_short_desc)
event.listen(ThermoDepositories, "before_insert", delete_empty_desc)


class ThermoData(SCHEMA_BASE):
    __tablename__ = "thermo_data_table"

    id = Column(Integer, primary_key=True)
    library_parent_id = mapped_column(ForeignKey("thermo_libraries_table.id"))
    group_parent_id = mapped_column(ForeignKey("groups_table.id"))
    depository_parent_id = mapped_column(ForeignKey("thermo_depositories_table.id"))
    
    Tdata_1 = Column(Float)
    Tdata_2 = Column(Float)
    Tdata_3 = Column(Float)
    Tdata_4 = Column(Float)
    Tdata_5 = Column(Float)
    Tdata_6 = Column(Float)
    Tdata_7 = Column(Float)
    Tdata_unit = Column(String)

    Cpdata_1 = Column(Float)
    Cpdata_2 = Column(Float)
    Cpdata_3 = Column(Float)
    Cpdata_4 = Column(Float)
    Cpdata_5 = Column(Float)
    Cpdata_6 = Column(Float)
    Cpdata_7 = Column(Float)
    Cpdata_unit = Column(String)
    
    Cpdata_unc_1 = Column(Float)
    Cpdata_unc_2 = Column(Float)
    Cpdata_unc_3 = Column(Float)
    Cpdata_unc_4 = Column(Float)
    Cpdata_unc_5 = Column(Float)
    Cpdata_unc_6 = Column(Float)
    Cpdata_unc_7 = Column(Float)

    H298 = Column(Float)
    H298_unit = Column(String)
    H298_unc = Column(Float)

    S298 = Column(Float)
    S298_unit = Column(String)
    S298_unc = Column(Float)


class Nasa(SCHEMA_BASE):
    __tablename__ = "nasa_table"

    id = Column(Integer, primary_key=True)
    library_parent_id = mapped_column(ForeignKey("thermo_libraries_table.id"))
    group_parent_id = mapped_column(ForeignKey("groups_table.id"))
    depository_parent_id = mapped_column(ForeignKey("thermo_depositories_table.id"))
    
    Tmin = Column(Float)
    Tmax = Column(Float)
    T_unit = Column(String)
    
    E0 = Column(Float)
    E0_unit = Column(String)
    
    Cp0 = Column(Float)
    Cp0_unit = Column(String)
    
    CpInf = Column(Float)
    CpInf_unit = Column(String)


class NasaPolynomial(SCHEMA_BASE):
    __tablename__ = "nasa_polynomial_table"

    id = Column(Integer, primary_key=True)
    nasa_id = mapped_column(ForeignKey("nasa_table.id"))
    
    c1 = Column(Float)
    c2 = Column(Float)
    c3 = Column(Float)
    c4 = Column(Float)
    c5 = Column(Float)
    c6 = Column(Float)
    c7 = Column(Float)
    
    Tmin = Column(Float)
    Tmax = Column(Float)
    T_unit = Column(String)
