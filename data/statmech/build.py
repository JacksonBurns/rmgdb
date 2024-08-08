from glob import glob
from pathlib import Path
from functools import partial

from schema import (
    GroupsTable,
    GroupsTreeTable,
    IdealGasTranslationTable,
    FrequencyTable,
    StatmechLibrariesTable,
    ConformerTable,
    NonlinearRotorTable,
    HarmonicOscillatorTable,
)


from sqlalchemy import create_engine, Column, Integer, String, Numeric, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from schema import Base


# Create engine and session
engine = create_engine("sqlite:///demo_v2.db", echo=False)
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)

# map the groups in...

# now map the libraries in


def ConformerSpoof(session, name, E0, modes, spin_multiplicity=None, optical_isomers=None):  # None for optional (nullable)
    global conformer_id_count
    global entry_count
    new_conformer = ConformerTable(
        id=conformer_id_count,
        parent_id=entry_count,
        energy=E0[0],
        energy_unit=E0[1],
        spin_multiplicity=spin_multiplicity,
        optical_isomers=optical_isomers,
    )
    conformer_id_count += 1
    session.add(new_conformer)


def IGSpoof(session, name, mass):
    global ig_id_count
    global conformer_id_count
    new_igt = IdealGasTranslationTable(
        id=ig_id_count,
        parent_id=conformer_id_count,
        mass=mass[0],
        mass_unit=mass[1],
    )
    ig_id_count += 1
    session.add(new_igt)


# spoof calls to entry function as rows in the library table
def LibrarySpoof(session, name, index, label, molecule, statmech, shortDesc, longDesc):
    global entry_count
    row = StatmechLibrariesTable(
        id=entry_count,
        name=name,
        short_description=shortDesc,
        long_description=longDesc,
        label=label,
        adjacency_list=molecule,
    )
    entry_count += 1
    session.add(row)


# global variable abuse
conformer_id_count = 0
ig_id_count = 0
entry_count = 0

library_dir = Path("./original/libraries")
for library_file in library_dir.glob("*debug*"):
    spoof_func = partial(LibrarySpoof, session, library_file.stem)
    conf_spoof = partial(ConformerSpoof, session, library_file.stem)
    ig_spoof = partial(IGSpoof, session, library_file.stem)
    exec(
        library_file.read_text(),
        {
            "entry": spoof_func,
            "conformer_id_count": conformer_id_count,
            "ig_id_count": ig_id_count,
            "entry_count": entry_count,
            "Conformer": conf_spoof,
            "IdealGasTranslation": ig_spoof,
        },
    )

try:
    session.commit()
except ValueError as e:
    session.rollback()
    print(f"Error: {e}")

session.close()
