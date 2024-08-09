from pathlib import Path

from rmgdb.statmech.schema import (
    # Group
    Groups,
    GroupsTree,
    GroupFrequency,
    Frequency,
    # Library
    IdealGasTranslation,
    StatmechLibraries,
    Conformer,
    NonlinearRotor,
    LinearRotor,
    HarmonicOscillator,
    # declarative SCHEMA_BASE,
    SCHEMA_BASE,
)


from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from rmgdatabase.common.tree_str_to_pairs import sketchy_conversion


# Create engine and SESSION
engine = create_engine("sqlite:///demo_v2.db", echo=False)
Session = sessionmaker(bind=engine)
SESSION = Session()
SCHEMA_BASE.metadata.create_all(engine)

LABEL_TO_DB_ID = {None: None}  # None: None for root/leaf nodes


# map the groups in...
def entry_spoof(*, index, label, group, statmech, shortDesc, longDesc):
    global ENTRY_COUNT
    global SESSION
    global CURRENT_NAME
    row = Groups(
        id=ENTRY_COUNT,
        name=CURRENT_NAME,
        short_description=shortDesc,
        long_description=longDesc,
        label=label,
        group=group,
    )
    LABEL_TO_DB_ID[label] = ENTRY_COUNT
    ENTRY_COUNT += 1
    SESSION.add(row)


def GroupFrequenciesSpoof(*, frequencies, symmetry):
    global ENTRY_COUNT
    global GROUP_FREQUENCIES_COUNT
    global FREQUENCIES_COUNT
    global SESSION
    row = GroupFrequency(
        id=ENTRY_COUNT,
        parent_id=ENTRY_COUNT,
        symmetry=symmetry,
    )
    SESSION.add(row)
    for freq_group in frequencies:
        row = Frequency(
            id=FREQUENCIES_COUNT,
            parent_id=GROUP_FREQUENCIES_COUNT,
            lower=freq_group[0],
            upper=freq_group[1],
            degeneracy=freq_group[2],
        )
        FREQUENCIES_COUNT += 1
    GROUP_FREQUENCIES_COUNT += 1


def tree_spoof(tree_str):
    global TREE_PAIRS_COUNT
    global SESSION
    pairs = sketchy_conversion(tree_str)
    for pair in pairs:
        row = GroupsTree(
            id=TREE_PAIRS_COUNT,
            parent_id=LABEL_TO_DB_ID[pair[0]],
            child_id=LABEL_TO_DB_ID[pair[1]],
        )
        SESSION.add(row)
        TREE_PAIRS_COUNT += 1


ENTRY_COUNT = 0
GROUP_FREQUENCIES_COUNT = 0
FREQUENCIES_COUNT = 0
TREE_PAIRS_COUNT = 0
group_dir = Path("./original/groups")
for group_file in group_dir.glob("*"):
    CURRENT_NAME = group_file.stem
    exec(
        group_file.read_text(),
        {  # we could just give our functions the exact same name as the file, but we do this for clarity/explicitness
            "entry": entry_spoof,
            "GroupFrequencies": GroupFrequenciesSpoof,
            "tree": tree_spoof,
        },
    )

# now map the libraries in


def ConformerSpoof(*, E0, modes, spin_multiplicity=None, optical_isomers=None):  # None for optional (nullable)
    global CONFORMER_COUNT
    global ENTRY_COUNT
    global SESSION
    new_conformer = Conformer(
        id=CONFORMER_COUNT,
        parent_id=ENTRY_COUNT,
        energy=E0[0],
        energy_unit=E0[1],
        spin_multiplicity=spin_multiplicity,
        optical_isomers=optical_isomers,
    )
    CONFORMER_COUNT += 1
    SESSION.add(new_conformer)


def HarmonicOscillatorSpoof(*, frequencies):
    global HARMONIC_OSCILLATOR_COUNT
    global CONFORMER_COUNT
    global SESSION
    new_igt = HarmonicOscillator(
        id=HARMONIC_OSCILLATOR_COUNT,
        parent_id=CONFORMER_COUNT,
        freq_unit=frequencies[1],
        freq_1=frequencies[0][0],
        # do the rest as well, allowing for not all to be filled
    )
    HARMONIC_OSCILLATOR_COUNT += 1
    SESSION.add(new_igt)


def IdealGasTranslationSpoof(*, mass):
    global IDEAL_GAS_TRANSLATION_COUNT
    global CONFORMER_COUNT
    global SESSION
    new_igt = IdealGasTranslation(
        id=IDEAL_GAS_TRANSLATION_COUNT,
        parent_id=CONFORMER_COUNT,
        mass=mass[0],
        mass_unit=mass[1],
    )
    IDEAL_GAS_TRANSLATION_COUNT += 1
    SESSION.add(new_igt)


def LinearRotorSpoof(*, inertia, symmetry):
    global LINEAR_ROTOR_COUNT
    global CONFORMER_COUNT
    global SESSION
    new_igt = LinearRotor(
        id=LINEAR_ROTOR_COUNT,
        parent_id=CONFORMER_COUNT,
        inertia=inertia[0],
        inertia_unit=inertia[1],
        symmetry=symmetry,
    )
    LINEAR_ROTOR_COUNT += 1
    SESSION.add(new_igt)


def NonlinearRotorSpoof(*, inertia, symmetry):
    global NONLINEAR_ROTOR_COUNT
    global CONFORMER_COUNT
    global SESSION
    new_igt = NonlinearRotor(
        id=NONLINEAR_ROTOR_COUNT,
        parent_id=CONFORMER_COUNT,
        inertia_x=inertia[0][0],
        inertia_y=inertia[0][1],
        inertia_z=inertia[0][2],
        inertia_unit=inertia[1],
        symmetry=symmetry,
    )
    NONLINEAR_ROTOR_COUNT += 1
    SESSION.add(new_igt)


def entry_spoof(*, index, label, molecule, statmech, shortDesc, longDesc):
    global ENTRY_COUNT
    global SESSION
    global CURRENT_NAME
    row = StatmechLibraries(
        id=ENTRY_COUNT,
        name=CURRENT_NAME,
        short_description=shortDesc,
        long_description=longDesc,
        label=label,
        adjacency_list=molecule,
    )
    ENTRY_COUNT += 1
    SESSION.add(row)


# global variable abuse
CONFORMER_COUNT = 0
IDEAL_GAS_TRANSLATION_COUNT = 0
ENTRY_COUNT = 0
LINEAR_ROTOR_COUNT = 0
NONLINEAR_ROTOR_COUNT = 0
HARMONIC_OSCILLATOR_COUNT = 0

library_dir = Path("./original/libraries")
for library_file in library_dir.glob("*"):
    CURRENT_NAME = library_file.stem
    exec(
        library_file.read_text(),
        {
            "entry": entry_spoof,
            "Conformer": ConformerSpoof,
            "IdealGasTranslation": IdealGasTranslationSpoof,
            "LinearRotor": LinearRotorSpoof,
            "NonlinearRotor": NonlinearRotorSpoof,
            "HarmonicOscillator": HarmonicOscillatorSpoof,
        },
    )

try:
    SESSION.commit()
except ValueError as e:
    SESSION.rollback()
    print(f"Error: {e}")


# make the views we need
conformer_view = (
    select(
        Conformer.parent_id.label("parent_id"),
        Conformer.energy.label("energy"),
        Conformer.energy_unit.label("energy_unit"),
        Conformer.spin_multiplicity.label("spin_multiplicity"),
        Conformer.optical_isomers.label("optical_isomers"),
        IdealGasTranslation.mass.label("mass"),
        IdealGasTranslation.mass_unit.label("mass_unit"),
        NonlinearRotor.inertia_x.label("inertia_x"),
        NonlinearRotor.inertia_y.label("inertia_y"),
        NonlinearRotor.inertia_z.label("inertia_z"),
        NonlinearRotor.inertia_unit.label("nonlinear_inertia_unit"),
        NonlinearRotor.symmetry.label("nonlinear_symmetry"),
        LinearRotor.inertia.label("linear_inertia"),
        LinearRotor.inertia_unit.label("linear_inertia_unit"),
        LinearRotor.symmetry.label("linear_symmetry"),
        HarmonicOscillator.freq_unit.label("harmonic_freq_unit"),
        HarmonicOscillator.freq_1.label("harmonic_freq_1"),
    )
    .select_from(
        Conformer,
    )
    .outerjoin(
        NonlinearRotor,
        # sqlalchemy should infer this auto-magically from the FK relationship
        # we give it anyway to make this relationship more explicit
        Conformer.id == NonlinearRotor.parent_id,
    )
    .outerjoin(
        LinearRotor,
        Conformer.id == LinearRotor.parent_id,
    )
    .outerjoin(
        HarmonicOscillator,
        Conformer.id == HarmonicOscillator.parent_id,
    )
    .outerjoin(
        IdealGasTranslation,
        Conformer.id == IdealGasTranslation.parent_id,
    )
).subquery("inner_t")


view_query = (
    select(
        StatmechLibraries.id,
        StatmechLibraries.name,
        StatmechLibraries.short_description,
        StatmechLibraries.long_description,
        StatmechLibraries.label,
        StatmechLibraries.adjacency_list,
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
        StatmechLibraries,
        StatmechLibraries.id == conformer_view.c.parent_id,
    )
)

# Create the view in the database
view_name = "statmech_libraries_view"
create_view_sql = text(f"CREATE VIEW {view_name} AS {view_query}")

Session = sessionmaker(bind=engine)
SESSION = Session()
SESSION.execute(create_view_sql)

SESSION.close()
