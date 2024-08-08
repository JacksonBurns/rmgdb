# todo: convert the spoofind functions to also deduce their name and the 'session' variable from the global namespace
# todo: make all the indexes into PKs since we build the views using those
# todo: spoof funcions should use * to force args to be passed as kewords to ensure they dont get processed incorrectly (probably not possible with sql anyway, though)
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
    LinearRotorTable,
    HarmonicOscillatorTable,
)


from sqlalchemy import create_engine, Column, Integer, String, Numeric, event, select, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from schema import Base


# Create engine and session
engine = create_engine("sqlite:///demo_v2.db", echo=False)
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)

# map the groups in...
def EntrySpoof(session, index, label, group, shortDesc, longDesc, symmetry=None):
    global entry_count
    row = FrequencyTable(
        id=index,
        name=name,
        short_description=shortDesc,
        long_description=longDesc,
        label=label,
        adjacency_list=molecule,
    )
    entry_count += 1
    session.add(row)
group_file = Path("./original/groups/groups.py")
spoof_func = partial(LibrarySpoof, session, library_file.stem)
conf_spoof = partial(ConformerSpoof, session, library_file.stem)
ig_spoof = partial(IGSpoof, session, library_file.stem)
linear_spoof = partial(LinearSpoof, session, library_file.stem)
nonlinear_spoof = partial(NonlinearSpoof, session, library_file.stem)
harmonic_spoof = partial(HarmonicSpoof, session, library_file.stem)
exec(
    library_file.read_text(),
    {
        "entry": spoof_func,
        "entry_count": entry_count,
        "Conformer": conf_spoof,
        "IdealGasTranslation": ig_spoof,
        "LinearRotor": linear_spoof,
        "NonlinearRotor": nonlinear_spoof,
        "HarmonicOscillator": harmonic_spoof,
    },
)

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


def HarmonicSpoof(session, name, frequencies):
    global harmonic_id_count
    global conformer_id_count
    new_igt = HarmonicOscillatorTable(
        id=harmonic_id_count,
        parent_id=conformer_id_count,
        freq_unit=frequencies[1],
        freq_1=frequencies[0][0],
        # do the rest as well, allowing for not all to be filled
    )
    harmonic_id_count += 1
    session.add(new_igt)


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


def LinearSpoof(session, name, inertia, symmetry):
    global linear_rotor_id_count
    global conformer_id_count
    new_igt = LinearRotorTable(
        id=linear_rotor_id_count,
        parent_id=conformer_id_count,
        inertia=inertia[0],
        inertia_unit=inertia[1],
        symmetry=symmetry,
    )
    linear_rotor_id_count += 1
    session.add(new_igt)


def NonlinearSpoof(session, name, inertia, symmetry):
    global nonlinear_rotor_id_count
    global conformer_id_count
    new_igt = NonlinearRotorTable(
        id=nonlinear_rotor_id_count,
        parent_id=conformer_id_count,
        inertia_x=inertia[0][0],
        inertia_y=inertia[0][1],
        inertia_z=inertia[0][2],
        inertia_unit=inertia[1],
        symmetry=symmetry,
    )
    nonlinear_rotor_id_count += 1
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
linear_rotor_id_count = 0
nonlinear_rotor_id_count = 0
harmonic_id_count = 0

library_dir = Path("./original/libraries")
for library_file in library_dir.glob("*"):
    spoof_func = partial(LibrarySpoof, session, library_file.stem)
    conf_spoof = partial(ConformerSpoof, session, library_file.stem)
    ig_spoof = partial(IGSpoof, session, library_file.stem)
    linear_spoof = partial(LinearSpoof, session, library_file.stem)
    nonlinear_spoof = partial(NonlinearSpoof, session, library_file.stem)
    harmonic_spoof = partial(HarmonicSpoof, session, library_file.stem)
    exec(
        library_file.read_text(),
        {
            "entry": spoof_func,
            "entry_count": entry_count,
            "Conformer": conf_spoof,
            "IdealGasTranslation": ig_spoof,
            "LinearRotor": linear_spoof,
            "NonlinearRotor": nonlinear_spoof,
            "HarmonicOscillator": harmonic_spoof,
        },
    )

try:
    session.commit()
except ValueError as e:
    session.rollback()
    print(f"Error: {e}")


# make the views we need
conformer_view = (
    select(
        ConformerTable.parent_id.label("parent_id"),
        ConformerTable.energy.label("energy"),
        ConformerTable.energy_unit.label("energy_unit"),
        ConformerTable.spin_multiplicity.label("spin_multiplicity"),
        ConformerTable.optical_isomers.label("optical_isomers"),
        IdealGasTranslationTable.mass.label("mass"),
        IdealGasTranslationTable.mass_unit.label("mass_unit"),
        NonlinearRotorTable.inertia_x.label("inertia_x"),
        NonlinearRotorTable.inertia_y.label("inertia_y"),
        NonlinearRotorTable.inertia_z.label("inertia_z"),
        NonlinearRotorTable.inertia_unit.label("nonlinear_inertia_unit"),
        NonlinearRotorTable.symmetry.label("nonlinear_symmetry"),
        LinearRotorTable.inertia.label("linear_inertia"),
        LinearRotorTable.inertia_unit.label("linear_inertia_unit"),
        LinearRotorTable.symmetry.label("linear_symmetry"),
        HarmonicOscillatorTable.freq_unit.label("harmonic_freq_unit"),
        HarmonicOscillatorTable.freq_1.label("harmonic_freq_1"),
    )
    .select_from(
        ConformerTable,
    )
    .outerjoin(
        NonlinearRotorTable,
        ConformerTable.id == NonlinearRotorTable.parent_id,  # sqlalchemy should infer this auto-magically from the FK relationship
    )
    .outerjoin(
        LinearRotorTable,
        ConformerTable.id == LinearRotorTable.parent_id,  # sqlalchemy should infer this auto-magically from the FK relationship
    )
    .outerjoin(
        HarmonicOscillatorTable,
        ConformerTable.id == HarmonicOscillatorTable.parent_id,  # sqlalchemy should infer this auto-magically from the FK relationship
    )
    .outerjoin(
        IdealGasTranslationTable,
        ConformerTable.id == IdealGasTranslationTable.parent_id,  # sqlalchemy should infer this auto-magically from the FK relationship
    )
).subquery("inner_t")


view_query = (
    select(
        StatmechLibrariesTable.id,
        StatmechLibrariesTable.name,
        StatmechLibrariesTable.short_description,
        StatmechLibrariesTable.long_description,
        StatmechLibrariesTable.label,
        StatmechLibrariesTable.adjacency_list,
        conformer_view.c.energy,
        conformer_view.c.energy_unit,
        conformer_view.c.spin_multiplicity,
        conformer_view.c.optical_isomers,
        conformer_view.c.mass,
        conformer_view.c.mass_unit,
        conformer_view.c.inertia_x,
        conformer_view.c.inertia_y,
        conformer_view.c.inertia_z,
        conformer_view.c.nonlinear_inertia_unit,
        conformer_view.c.nonlinear_symmetry,
        conformer_view.c.linear_inertia,
        conformer_view.c.linear_inertia_unit,
        conformer_view.c.linear_symmetry,
        conformer_view.c.harmonic_freq_unit,
        conformer_view.c.harmonic_freq_1,
    )
    .select_from(
        conformer_view,
    )
    .outerjoin(
        StatmechLibrariesTable,
        StatmechLibrariesTable.id == conformer_view.c.parent_id,
    )
)

# Create the view in the database
view_name = "statmech_libraries_view"
create_view_sql = text(f"CREATE VIEW {view_name} AS {view_query}")

Session = sessionmaker(bind=engine)
session = Session()
session.execute(create_view_sql)

session.close()
