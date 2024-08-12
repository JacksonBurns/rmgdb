import math
from pathlib import Path

import yaml
import pandas as pd
from tqdm import tqdm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
from rmgdb.statmech.views import statmech_groups_view_sql, statmech_libraries_view_sql, label_pairs_view_sql


# fix multiline string printing
# from: https://opendev.org/airship/pegleg/commit/18598b671bc67542e14bab8aadfcb9f806fd0e14
# never merged into pyyaml
yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str
repr_str = lambda dumper, data: (  # noqa: E731
    dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|") if "\n" in data else dumper.org_represent_str(data)
)
yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)


def dump_db():
    # save each library to its own file
    all_libraries_df = pd.read_sql("SELECT * FROM statmech_libraries_view", "sqlite:///statmech.db")
    for library_name, library_df in tqdm(all_libraries_df.groupby("name"), desc="Generating libraries"):
        all_rows = []
        for _, row in library_df.iterrows():
            formatted_dict = dict(
                # don't keep the internal database id in the text dump
                # id=row.id
                short_description=row.short_description,
                long_description=row.long_description,
                label=row.label,
                adjacency_list=row.adjacency_list,
                statmech=dict(
                    energy=row.energy,
                    energy_unit=row.energy_unit,
                    modes=dict(),
                ),
            )
            # add the optional rows
            if row.mass_unit is not None:
                formatted_dict["statmech"]["modes"]["ideal_gas_translation"] = dict(
                    mass=row.mass,
                    mass_unit=row.mass_unit,
                )
            if row.nonlinear_inertia_unit is not None:
                formatted_dict["statmech"]["modes"]["nonlinear_rotor"] = dict(
                    inertia_x=row.inertia_x,
                    inertia_y=row.inertia_y,
                    inertia_z=row.inertia_z,
                    nonlinear_inertia_unit=row.nonlinear_inertia_unit,
                    nonlinear_symmetry=row.nonlinear_symmetry,
                )
            if row.linear_inertia_unit is not None:
                formatted_dict["statmech"]["modes"]["linear_rotor"] = dict(
                    linear_inertia=row.linear_inertia,
                    linear_inertia_unit=row.linear_inertia_unit,
                    linear_symmetry=row.linear_symmetry,
                )
            if row.harmonic_freq_unit is not None:
                formatted_dict["statmech"]["modes"]["harmonic_oscillator"] = dict(
                    harmonic_freq_unit=row.harmonic_freq_unit,
                    harmonic_freq_1=row.harmonic_freq_1,
                    harmonic_freq_2=row.harmonic_freq_2,
                    harmonic_freq_3=row.harmonic_freq_3,
                    harmonic_freq_4=row.harmonic_freq_4,
                    harmonic_freq_5=row.harmonic_freq_5,
                    harmonic_freq_6=row.harmonic_freq_6,
                    harmonic_freq_7=row.harmonic_freq_7,
                    harmonic_freq_8=row.harmonic_freq_8,
                    harmonic_freq_9=row.harmonic_freq_9,
                    harmonic_freq_10=row.harmonic_freq_10,
                    harmonic_freq_11=row.harmonic_freq_11,
                    harmonic_freq_12=row.harmonic_freq_12,
                )
                to_pop = []
                for key, value in formatted_dict["statmech"]["modes"]["harmonic_oscillator"].items():
                    if not isinstance(value, str) and math.isnan(value):
                        to_pop.append(key)
                for key in to_pop:
                    formatted_dict["statmech"]["modes"]["harmonic_oscillator"].pop(key)
            all_rows.append(formatted_dict)

        with open(Path(f"yml/libraries/{library_name}.yml"), "w") as f:
            yaml.dump_all(all_rows, f, yaml.SafeDumper, sort_keys=False)

    # do the same for groups
    all_groups_df = pd.read_sql("SELECT * FROM statmech_groups_view", "sqlite:///statmech.db")
    for group_name, group_df in tqdm(all_groups_df.groupby("name"), desc="Generating groups"):
        all_rows = []
        # re-gather the frequencies
        freq_groups = group_df.groupby(
            ["name", "short_description", "long_description", "label", "group", "symmetry"],
            dropna=False,  # don't drop rows which have no statmech at all
        ).agg(list)
        for index_tuple, frequency_series in freq_groups.iterrows():
            # lookup the children of this parent
            group_pairs = pd.read_sql(
                f"SELECT child_label from label_pairs_view WHERE label_pairs_view.parent_label = '{index_tuple[3]}'",
                "sqlite:///statmech.db",
            )
            statmech_dict = (
                None
                if math.isnan(frequency_series.lower[0])
                else dict(
                    symmetry=index_tuple[5],
                    frequencies=[
                        dict(lower=low, upper=up, degeneracy=deg)
                        for low, up, deg in zip(frequency_series.lower, frequency_series.upper, frequency_series.degeneracy, strict=True)
                    ],
                )
            )
            formatted_dict = dict(
                # don't keep the internal database id in the text dump
                # id=row.id
                label=index_tuple[3],
                children=group_pairs["child_label"].to_list(),
                short_description=index_tuple[1],
                long_description=index_tuple[2],
                group=index_tuple[4],
                statmech=statmech_dict,
            )
            all_rows.append(formatted_dict)

        with open(Path(f"yml/groups/{group_name}.yml"), "w") as f:
            yaml.dump_all(all_rows, f, yaml.SafeDumper, sort_keys=False)


# SQl should give the errors if data is improperly provided - just need to design triggers and
# ddl well enough and then pass them through in a sensible way here
def gen_db():
    # connect to the database
    engine = create_engine("sqlite:///statmech.db", echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    SCHEMA_BASE.metadata.create_all(engine)

    # initialize counters
    entry_counter = 0
    statmech_counter = 0
    ideal_gas_counter = 0
    nonlinear_rotor_counter = 0
    linear_rotor_counter = 0
    harmonic_oscillator_counter = 0

    # load the libraries
    library_dir = Path("./yml/libraries")
    for library_file in tqdm(library_dir.glob("*"), desc="Loading libraries"):
        with open(library_file, "r") as f:
            all_rows = list(yaml.safe_load_all(f))
        for row in all_rows:
            # do the inverse mapping, use counters to rebuild the internal index
            new_row = StatmechLibraries(
                id=entry_counter,
                name=library_file.stem,
                short_description=row["short_description"],
                long_description=row["long_description"],
                label=row["label"],
                adjacency_list=row["adjacency_list"],
            )
            session.add(new_row)
            statmech_dict = row.get("statmech", False)
            if statmech_dict:
                new_row = Conformer(
                    id=statmech_counter,
                    parent_id=entry_counter,
                    energy=statmech_dict["energy"],
                    energy_unit=statmech_dict["energy_unit"],
                    spin_multiplicity=statmech_dict.get("spin_multiplicity", None),
                )
                session.add(new_row)
                modes_dict = statmech_dict["modes"]
                if modes_dict.get("ideal_gas_translation", False):
                    new_row = IdealGasTranslation(
                        id=ideal_gas_counter,
                        parent_id=statmech_counter,
                        mass=modes_dict["ideal_gas_translation"]["mass"],
                        mass_unit=modes_dict["ideal_gas_translation"]["mass_unit"],
                    )
                    session.add(new_row)
                    ideal_gas_counter += 1
                if modes_dict.get("linear_rotor", False):
                    new_row = LinearRotor(
                        id=linear_rotor_counter,
                        parent_id=statmech_counter,
                        inertia=modes_dict["linear_rotor"]["linear_inertia"],
                        inertia_unit=modes_dict["linear_rotor"]["linear_inertia_unit"],
                        symmetry=modes_dict["linear_rotor"]["linear_symmetry"],
                    )
                    session.add(new_row)
                    linear_rotor_counter += 1
                if modes_dict.get("nonlinear_rotor", False):
                    new_row = NonlinearRotor(
                        id=nonlinear_rotor_counter,
                        parent_id=statmech_counter,
                        inertia_x=modes_dict["nonlinear_rotor"]["inertia_x"],
                        inertia_y=modes_dict["nonlinear_rotor"]["inertia_y"],
                        inertia_z=modes_dict["nonlinear_rotor"]["inertia_z"],
                        inertia_unit=modes_dict["nonlinear_rotor"]["nonlinear_inertia_unit"],
                        symmetry=modes_dict["nonlinear_rotor"]["nonlinear_symmetry"],
                    )
                    session.add(new_row)
                    nonlinear_rotor_counter += 1
                if modes_dict.get("harmonic_oscillator", False):
                    new_row = HarmonicOscillator(
                        id=harmonic_oscillator_counter,
                        parent_id=statmech_counter,
                        freq_unit=modes_dict["harmonic_oscillator"]["harmonic_freq_unit"],
                        freq_1=modes_dict["harmonic_oscillator"]["harmonic_freq_1"],
                        freq_2=modes_dict["harmonic_oscillator"].get("harmonic_freq_2", None),
                        freq_3=modes_dict["harmonic_oscillator"].get("harmonic_freq_3", None),
                        freq_4=modes_dict["harmonic_oscillator"].get("harmonic_freq_4", None),
                        freq_5=modes_dict["harmonic_oscillator"].get("harmonic_freq_5", None),
                        freq_6=modes_dict["harmonic_oscillator"].get("harmonic_freq_6", None),
                        freq_7=modes_dict["harmonic_oscillator"].get("harmonic_freq_7", None),
                        freq_8=modes_dict["harmonic_oscillator"].get("harmonic_freq_8", None),
                        freq_9=modes_dict["harmonic_oscillator"].get("harmonic_freq_9", None),
                        freq_10=modes_dict["harmonic_oscillator"].get("harmonic_freq_10", None),
                        freq_11=modes_dict["harmonic_oscillator"].get("harmonic_freq_11", None),
                        freq_12=modes_dict["harmonic_oscillator"].get("harmonic_freq_12", None),
                    )
                    session.add(new_row)
                    harmonic_oscillator_counter += 1
                statmech_counter += 1
            entry_counter += 1

        # and the groups
        library_dir = Path("./yml/libraries")

    # MOAR counters
    entry_count = 0
    group_frequencies_count = 0
    frequencies_count = 0
    tree_count = 0

    # label to id lookup for building the pair table
    label_to_id = {None: None}

    # and now load the groups
    group_dir = Path("./yml/groups")
    for group_file in tqdm(group_dir.glob("*"), desc="Loading groups"):
        with open(group_file, "r") as f:
            all_rows = list(yaml.safe_load_all(f))
        for row in all_rows:
            label_to_id[row["label"]] = entry_count
            new_row = Groups(
                id=entry_count,
                name=group_file.stem,
                short_description=row["short_description"],
                long_description=row["long_description"],
                label=row["label"],
                group=row["group"],
            )
            session.add(new_row)

            statmech_dict = row.get("statmech", False)
            if statmech_dict:
                new_row = GroupFrequency(
                    id=group_frequencies_count,
                    parent_id=entry_count,
                    symmetry=statmech_dict["symmetry"],
                )
                session.add(new_row)
                for freq_dict in statmech_dict["frequencies"]:
                    new_row = Frequency(
                        id=frequencies_count,
                        parent_id=group_frequencies_count,
                        lower=freq_dict["lower"],
                        upper=freq_dict["upper"],
                        degeneracy=freq_dict["degeneracy"],
                    )
                    session.add(new_row)
                    frequencies_count += 1
                group_frequencies_count += 1
            entry_count += 1

        # iterate again to build the pair table now that the label_to_id dict is filled
        for row in all_rows:
            for child_label in row["children"]:
                new_row = GroupsTree(
                    id=tree_count,
                    parent_id=label_to_id[row["label"]],
                    child_id=label_to_id[child_label],
                )
                session.add(new_row)
                tree_count += 1

    try:
        session.commit()
    except ValueError as e:
        session.rollback()
        print(f"Error: {e}")

    session.execute(statmech_groups_view_sql)
    session.execute(statmech_libraries_view_sql)
    session.execute(label_pairs_view_sql)

    session.close()


if __name__ == "__main__":
    dump_db()
    Path("statmech.db").rename("old.db")
    gen_db()
