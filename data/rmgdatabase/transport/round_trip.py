import math
from pathlib import Path

import yaml
import pandas as pd
from tqdm import tqdm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rmgdb.transport.schema import (
    # Group
    Groups,
    GroupsTree,
    CriticalPointGroupContribution,
    # Library
    TransportLibraries,
    TransportData,
    # declarative SCHEMA_BASE
    SCHEMA_BASE,
)
from rmgdb.transport.views import (
    transport_groups_view_sql,
    transport_libraries_view_sql,
    label_pairs_view_sql,
)

# fix multiline string printing
# from: https://opendev.org/airship/pegleg/commit/18598b671bc67542e14bab8aadfcb9f806fd0e14
# never merged into pyyaml
yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str
repr_str = lambda dumper, data: (  # noqa: E731
    dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|") if "\n" in data else dumper.org_represent_str(data)
)
yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)


def dump_db():
    Path("yml/libraries").mkdir(parents=True, exist_ok=True)
    Path("yml/groups").mkdir(parents=True, exist_ok=True)

    # 1. save each library to its own file
    all_libraries_df = pd.read_sql("SELECT * FROM transport_libraries_view", "sqlite:///transport.db")
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
            )
            
            # Check if transport data exists by verifying shapeIndex is not NaN/None
            if not pd.isna(row.shapeIndex):
                formatted_dict["transport"] = dict(
                    shapeIndex=int(row.shapeIndex),
                    epsilon=row.epsilon,
                    epsilon_unit=row.epsilon_unit,
                    sigma=row.sigma,
                    sigma_unit=row.sigma_unit,
                    dipoleMoment=row.dipoleMoment,
                    dipoleMoment_unit=row.dipoleMoment_unit,
                    polarizability=row.polarizability,
                    polarizability_unit=row.polarizability_unit,
                    rotrelaxcollnum=row.rotrelaxcollnum,
                )
            
            all_rows.append(formatted_dict)

        with open(Path(f"yml/libraries/{library_name}.yml"), "w") as f:
            yaml.dump_all(all_rows, f, yaml.SafeDumper, sort_keys=False)

    # 2. do the same for groups
    all_groups_df = pd.read_sql("SELECT * FROM transport_groups_view", "sqlite:///transport.db")
    for group_name, group_df in tqdm(all_groups_df.groupby("name"), desc="Generating groups"):
        all_rows = []
        for _, row in group_df.iterrows():
            # lookup the children of this parent
            group_pairs = pd.read_sql(
                f"SELECT child_label from label_pairs_view WHERE label_pairs_view.parent_label = '{row.label}'",
                "sqlite:///transport.db",
            )
            
            transport_group_dict = None
            # Check if group contribution exists by verifying Tc is not NaN/None
            if not pd.isna(row.Tc):
                transport_group_dict = dict(
                    Tc=row.Tc,
                    Pc=row.Pc,
                    Vc=row.Vc,
                    Tb=row.Tb,
                    structureIndex=int(row.structureIndex) if not pd.isna(row.structureIndex) else None,
                )
            
            formatted_dict = dict(
                # don't keep the internal database id in the text dump
                # id=row.id
                label=row.label,
                children=group_pairs["child_label"].to_list(),
                short_description=row.short_description,
                long_description=row.long_description,
                group=row["group"],
                transportGroup=transport_group_dict,
            )
            all_rows.append(formatted_dict)

        with open(Path(f"yml/groups/{group_name}.yml"), "w") as f:
            yaml.dump_all(all_rows, f, yaml.SafeDumper, sort_keys=False)


# SQL should give the errors if data is improperly provided - just need to design triggers and
# ddl well enough and then pass them through in a sensible way here
def gen_db():
    # connect to the database
    engine = create_engine("sqlite:///transport.db", echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    SCHEMA_BASE.metadata.create_all(engine)

    # initialize counters
    library_counter = 0
    transport_data_counter = 0
    group_counter = 0
    cpgc_counter = 0
    tree_count = 0

    # load the libraries
    library_dir = Path("./yml/libraries")
    if library_dir.exists():
        for library_file in tqdm(library_dir.glob("*.yml"), desc="Loading libraries"):
            with open(library_file, "r") as f:
                all_rows = list(yaml.safe_load_all(f))
            for row in all_rows:
                # do the inverse mapping, use counters to rebuild the internal index
                new_row = TransportLibraries(
                    id=library_counter,
                    name=library_file.stem,
                    short_description=row.get("short_description", ""),
                    long_description=row.get("long_description", ""),
                    label=row["label"],
                    adjacency_list=row["adjacency_list"],
                )
                session.add(new_row)
                
                transport_dict = row.get("transport", False)
                if transport_dict:
                    new_td = TransportData(
                        id=transport_data_counter,
                        parent_id=library_counter,
                        shapeIndex=transport_dict.get("shapeIndex"),
                        epsilon=transport_dict.get("epsilon"),
                        epsilon_unit=transport_dict.get("epsilon_unit"),
                        sigma=transport_dict.get("sigma"),
                        sigma_unit=transport_dict.get("sigma_unit"),
                        dipoleMoment=transport_dict.get("dipoleMoment"),
                        dipoleMoment_unit=transport_dict.get("dipoleMoment_unit"),
                        polarizability=transport_dict.get("polarizability"),
                        polarizability_unit=transport_dict.get("polarizability_unit"),
                        rotrelaxcollnum=transport_dict.get("rotrelaxcollnum"),
                    )
                    session.add(new_td)
                    transport_data_counter += 1
                library_counter += 1


    # label to id lookup for building the pair table
    label_to_id = {None: None}

    # and now load the groups
    group_dir = Path("./yml/groups")
    if group_dir.exists():
        for group_file in tqdm(group_dir.glob("*.yml"), desc="Loading groups"):
            with open(group_file, "r") as f:
                all_rows = list(yaml.safe_load_all(f))
            for row in all_rows:
                label_to_id[row["label"]] = group_counter
                new_row = Groups(
                    id=group_counter,
                    name=group_file.stem,
                    short_description=row.get("short_description", ""),
                    long_description=row.get("long_description", ""),
                    label=row["label"],
                    group=row["group"],
                )
                session.add(new_row)

                cpgc_dict = row.get("transportGroup", False)
                if cpgc_dict:
                    new_cpgc = CriticalPointGroupContribution(
                        id=cpgc_counter,
                        parent_id=group_counter,
                        Tc=cpgc_dict.get("Tc"),
                        Pc=cpgc_dict.get("Pc"),
                        Vc=cpgc_dict.get("Vc"),
                        Tb=cpgc_dict.get("Tb"),
                        structureIndex=cpgc_dict.get("structureIndex"),
                    )
                    session.add(new_cpgc)
                    cpgc_counter += 1
                group_counter += 1

            # iterate again to build the pair table now that the label_to_id dict is filled
            for row in all_rows:
                for child_label in row.get("children", []):
                    new_tree = GroupsTree(
                        id=tree_count,
                        parent_id=label_to_id[row["label"]],
                        child_id=label_to_id[child_label],
                    )
                    session.add(new_tree)
                    tree_count += 1

    try:
        session.commit()
    except ValueError as e:
        session.rollback()
        print(f"Error: {e}")

    session.execute(transport_groups_view_sql)
    session.execute(transport_libraries_view_sql)
    session.execute(label_pairs_view_sql)

    session.close()


if __name__ == "__main__":
    dump_db()
    
    # After dumping, optionally test that the generation logic succeeds
    Path("transport.db").rename("old.db")
    gen_db()
