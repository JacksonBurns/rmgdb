from sqlalchemy import (
    Column,
    Integer,
    String,
    event,
    SmallInteger,
    ForeignKey,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column

from rmgdb.solvation.triggers import (
    check_short_desc,
    delete_empty_desc,
    validate_solvent_parameters,
    validate_data_count,
)

SCHEMA_BASE = declarative_base()


# groups and associated tables
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

# libraries and associated tables
class SolvationLibraries(SCHEMA_BASE):
    __tablename__ = "solvation_libraries_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    molecule = Column(String)


event.listen(SolvationLibraries, "before_insert", check_short_desc)
event.listen(SolvationLibraries, "before_insert", delete_empty_desc)


class SoluteLibrary(SCHEMA_BASE):
    __tablename__ = "solute_library_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    molecule = Column(String)


event.listen(SoluteLibrary, "before_insert", check_short_desc)
event.listen(SoluteLibrary, "before_insert", delete_empty_desc)

class SolventLibrary(SCHEMA_BASE):
    __tablename__ = "solvent_library_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    adjacency_list = Column(String)


event.listen(SolventLibrary, "before_insert", check_short_desc)
event.listen(SolventLibrary, "before_insert", delete_empty_desc)
event.listen(SolventLibrary, "before_insert", validate_solvent_parameters)


class SoluteData(SCHEMA_BASE):
    __tablename__ = "solute_data_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("groups_table.id"))  # Link to groups for group data
    # Abraham solute parameters
    S = Column(Float)  # S parameter (dipolarity/polarizability)
    B = Column(Float)  # B parameter (basicity)
    E = Column(Float)  # E parameter (excess molar refraction)
    L = Column(Float)  # L parameter (gas-hexadecane partition coefficient)
    A = Column(Float)  # A parameter (hydrogen bond acidity)
    V = Column(Float)  # V parameter (McGowan characteristic volume)

class SoluteLibraryData(SCHEMA_BASE):
    __tablename__ = "solute_library_data_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("solute_library_table.id"))  # Link to solute library
    # Abraham solute parameters
    S = Column(Float)  # S parameter (dipolarity/polarizability)
    B = Column(Float)  # B parameter (basicity)
    E = Column(Float)  # E parameter (excess molar refraction)
    L = Column(Float)  # L parameter (gas-hexadecane partition coefficient)
    A = Column(Float)  # A parameter (hydrogen bond acidity)
    V = Column(Float)  # V parameter (McGowan characteristic volume)

class SolventData(SCHEMA_BASE):
    __tablename__ = "solvent_data_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("solvent_library_table.id"))
    
    # Abraham gas-to-solvent parameters for solvation free energy (dGsolv) correction at 298K
    s_g = Column(Float)  # s parameter for dGsolv
    b_g = Column(Float)  # b parameter for dGsolv
    e_g = Column(Float)  # e parameter for dGsolv
    l_g = Column(Float)  # l parameter for dGsolv
    a_g = Column(Float)  # a parameter for dGsolv
    c_g = Column(Float)  # c parameter for dGsolv
    
    # Mintz parameters for solvation enthalpy (dHsolv) correction at 298K
    s_h = Column(Float)  # s parameter for dHsolv
    b_h = Column(Float)  # b parameter for dHsolv
    e_h = Column(Float)  # e parameter for dHsolv
    l_h = Column(Float)  # l parameter for dHsolv
    a_h = Column(Float)  # a parameter for dHsolv
    c_h = Column(Float)  # c parameter for dHsolv
    
    # Viscosity parameters
    A = Column(Float)  # Viscosity parameter A
    B = Column(Float)  # Viscosity parameter B
    C = Column(Float)  # Viscosity parameter C
    D = Column(Float)  # Viscosity parameter D
    E = Column(Float)  # Viscosity parameter E
    
    # Additional properties
    alpha = Column(Float)  # SOLUTE parameter A for H-abstraction rxns
    beta = Column(Float)  # SOLUTE parameter B for H-abstraction rxns
    eps = Column(Float)  # Dielectric constant
    name_in_coolprop = Column(String)  # Name used in CoolProp package


class DataCountGAV(SCHEMA_BASE):
    __tablename__ = "data_count_gav_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("groups_table.id"))
    
    # Data counts for each Abraham parameter
    S = Column(Integer)  # Number of data points for S parameter
    B = Column(Integer)  # Number of data points for B parameter
    E = Column(Integer)  # Number of data points for E parameter
    L = Column(Integer)  # Number of data points for L parameter
    A = Column(Integer)  # Number of data points for A parameter


event.listen(DataCountGAV, "before_insert", validate_data_count)


class DataCountSolvent(SCHEMA_BASE):
    __tablename__ = "data_count_solvent_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("solvent_library_table.id"))
    
    # Data quality metrics
    dGsolvCount = Column(Integer)  # Number of data points for dGsolv fitting
    dGsolvMAE_value = Column(Float)  # Mean absolute error for dGsolv
    dGsolvMAE_unit = Column(String)  # Unit for dGsolv MAE
    dHsolvCount = Column(Integer)  # Number of data points for dHsolv fitting
    dHsolvMAE_value = Column(Float)  # Mean absolute error for dHsolv
    dHsolvMAE_unit = Column(String)  # Unit for dHsolv MAE

event.listen(DataCountSolvent, "before_insert", validate_data_count)
