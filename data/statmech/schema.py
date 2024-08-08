# this belongs in rmgdb/statmech - putting here for ease of import while this package is not yet installable

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

Base = declarative_base()


# groups and associated tables
class GroupsTable(Base):
    __tablename__ = "groups_table"

    id = Column(Integer, primary_key=True)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    group = Column(String)
    symmetry = Column(SmallInteger)


def check_short_desc(mapper, connection, target):
    if len(target.short_description) > 20:
        raise ValueError("Short description must be <20 characters - use long description.")


event.listen(GroupsTable, "before_insert", check_short_desc)


class GroupsTreeTable(Base):
    __tablename__ = "groups_tree_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("groups_table.id"))
    child_id = mapped_column(ForeignKey("groups_table.id"))


class FrequencyTable(Base):
    __tablename__ = "frequency_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("groups_table.id"))
    frequency_part_1 = Column(SmallInteger)
    frequency_part_2 = Column(SmallInteger)
    frequency_part_3 = Column(SmallInteger)


# libraries and associated tables
class StatmechLibrariesTable(Base):
    __tablename__ = "statmech_libraries_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    label = Column(String)
    adjacency_list = Column(String)


class ConformerTable(Base):
    __tablename__ = "conformer_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("statmech_libraries_table.id"))
    energy = Column(Float)
    energy_unit = Column(String)  # validate that it is a supported unit
    spin_multiplicity = Column(Integer)
    optical_isomers = Column(Integer)


class IdealGasTranslationTable(Base):
    __tablename__ = "ideal_gas_translation_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("conformer_table.id"))
    mass = Column(Float)
    mass_unit = Column(String)


class NonlinearRotorTable(Base):
    __tablename__ = "nonlinear_rotor_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("conformer_table.id"))

    interia_x = Column(Float)
    inertia_y = Column(Float)
    inertia_z = Column(Float)
    inertia_unit = Column(String)
    symmetry = Column(SmallInteger)


class HarmonicOscillatorTable:
    pass
