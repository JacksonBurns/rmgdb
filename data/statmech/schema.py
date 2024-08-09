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


def check_short_desc(mapper, connection, target):
    if len(target.short_description) > 20:
        print("Truncating short description (consider using long).")
        target.short_description = target.short_description[0:20]


event.listen(GroupsTable, "before_insert", check_short_desc)


class GroupsTreeTable(Base):
    __tablename__ = "groups_tree_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("groups_table.id"))
    child_id = mapped_column(ForeignKey("groups_table.id"))

class GroupFrequencyTable(Base):
    __tablename__ = "group_frequency_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("groups_table.id"))
    symmetry = Column(SmallInteger)

class FrequencyTable(Base):
    __tablename__ = "frequency_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("group_frequency_table.id"))
    lower = Column(SmallInteger)
    upper = Column(SmallInteger)
    degeneracy = Column(SmallInteger)


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

    inertia_x = Column(Float)
    inertia_y = Column(Float)
    inertia_z = Column(Float)
    inertia_unit = Column(String)
    symmetry = Column(SmallInteger)


class LinearRotorTable(Base):
    __tablename__ = "linear_rotor_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("conformer_table.id"))

    inertia = Column(Float)
    inertia_unit = Column(String)
    symmetry = Column(SmallInteger)


class HarmonicOscillatorTable(Base):
    __tablename__ = "harmonic_oscillator_table"

    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("conformer_table.id"))

    freq_unit = Column(String)
    freq_1 = Column(Float)
    freq_2 = Column(Float)
    freq_3 = Column(Float)
    freq_4 = Column(Float)
    freq_5 = Column(Float)
    freq_6 = Column(Float)
    freq_7 = Column(Float)
    freq_8 = Column(Float)
    freq_9 = Column(Float)
    freq_10 = Column(Float)
    freq_11 = Column(Float)
    freq_12 = Column(Float)
