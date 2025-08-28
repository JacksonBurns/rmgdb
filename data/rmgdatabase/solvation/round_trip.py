import math
from pathlib import Path

import yaml
import pandas as pd
from tqdm import tqdm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rmgdb.solvation.schema import (
    # Group
    Groups,
    GroupsTree,
    SoluteData,
    DataCountGAV,
    # Library
    SolvationLibraries,
    SoluteLibrary,
    SolventLibrary,
    SolventData,
    DataCountSolvent,
    # declarative SCHEMA_BASE,
    SCHEMA_BASE,
)
from rmgdb.solvation.views import solvation_groups_view_sql, solute_libraries_view_sql, solvent_libraries_view_sql, label_pairs_view_sql


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
    # Query solute and solvent libraries separately since they have different column structures
    solute_libraries_df = pd.read_sql("SELECT * FROM solute_libraries_view", "sqlite:///solvation.db")
    solvent_libraries_df = pd.read_sql("SELECT * FROM solvent_libraries_view", "sqlite:///solvation.db")
    
    # Combine them into a single DataFrame with consistent columns
    all_libraries_df = pd.concat([solute_libraries_df, solvent_libraries_df], ignore_index=True)
    
    for library_name, library_df in tqdm(all_libraries_df.groupby("name"), desc="Generating libraries"):
        all_rows = []
        for _, row in library_df.iterrows():
            formatted_dict = dict(
                # don't keep the internal database id in the text dump
                # id=row.id
                short_description=row.short_description,
                long_description=row.long_description,
                label=row.label,
                molecule=row.molecule,
            )
            
            # Add solute data if present
            if not math.isnan(row.S) if hasattr(row, 'S') else True:
                formatted_dict["solute"] = dict(
                    S=row.S if hasattr(row, 'S') else None,
                    B=row.B if hasattr(row, 'B') else None,
                    E=row.E if hasattr(row, 'E') else None,
                    L=row.L if hasattr(row, 'L') else None,
                    A=row.A if hasattr(row, 'A') else None,
                    V=row.V if hasattr(row, 'V') else None,
                )
                # Remove None values
                formatted_dict["solute"] = {k: v for k, v in formatted_dict["solute"].items() if v is not None}
            
            # Add solvent data if present
            if not math.isnan(row.s_g) if hasattr(row, 's_g') else True:
                formatted_dict["solvent"] = dict(
                    s_g=row.s_g if hasattr(row, 's_g') else None,
                    b_g=row.b_g if hasattr(row, 'b_g') else None,
                    e_g=row.e_g if hasattr(row, 'e_g') else None,
                    l_g=row.l_g if hasattr(row, 'l_g') else None,
                    a_g=row.a_g if hasattr(row, 'a_g') else None,
                    c_g=row.c_g if hasattr(row, 'c_g') else None,
                    s_h=row.s_h if hasattr(row, 's_h') else None,
                    b_h=row.b_h if hasattr(row, 'b_h') else None,
                    e_h=row.e_h if hasattr(row, 'e_h') else None,
                    l_h=row.l_h if hasattr(row, 'l_h') else None,
                    a_h=row.a_h if hasattr(row, 'a_h') else None,
                    c_h=row.c_h if hasattr(row, 'c_h') else None,
                    A=row.A if hasattr(row, 'A') else None,
                    B=row.B if hasattr(row, 'B') else None,
                    C=row.C if hasattr(row, 'C') else None,
                    D=row.D if hasattr(row, 'D') else None,
                    E=row.E if hasattr(row, 'E') else None,
                    alpha=row.alpha if hasattr(row, 'alpha') else None,
                    beta=row.beta if hasattr(row, 'beta') else None,
                    eps=row.eps if hasattr(row, 'eps') else None,
                    name_in_coolprop=row.name_in_coolprop if hasattr(row, 'name_in_coolprop') else None,
                )
                # Remove None values
                formatted_dict["solvent"] = {k: v for k, v in formatted_dict["solvent"].items() if v is not None}
                
                # Add data count if present
                if not math.isnan(row.dGsolvCount) if hasattr(row, 'dGsolvCount') else True:
                    formatted_dict["dataCount"] = dict(
                        dGsolvCount=row.dGsolvCount if hasattr(row, 'dGsolvCount') else None,
                        dGsolvMAE=(row.dGsolvMAE_value, row.dGsolvMAE_unit) if hasattr(row, 'dGsolvMAE_value') else None,
                        dHsolvCount=row.dHsolvCount if hasattr(row, 'dHsolvCount') else None,
                        dHsolvMAE=(row.dHsolvMAE_value, row.dHsolvMAE_unit) if hasattr(row, 'dHsolvMAE_value') else None,
                    )
                    # Remove None values
                    formatted_dict["dataCount"] = {k: v for k, v in formatted_dict["dataCount"].items() if v is not None}
            
            all_rows.append(formatted_dict)

        with open(Path(f"yml/libraries/{library_name}.yml"), "w") as f:
            yaml.dump_all(all_rows, f, yaml.SafeDumper, sort_keys=False)

    # do the same for groups
    all_groups_df = pd.read_sql("SELECT * FROM solvation_groups_view", "sqlite:///solvation.db")
    for group_name, group_df in tqdm(all_groups_df.groupby("name"), desc="Generating groups"):
        all_rows = []
        # re-gather the solute data
        solute_groups = group_df.groupby(
            ["name", "short_description", "long_description", "label", "group"],
            dropna=False,  # don't drop rows which have no solvation data at all
        ).agg(list)
        for index_tuple, solute_series in solute_groups.iterrows():
            # lookup the children of this parent
            group_pairs = pd.read_sql(
                f"SELECT child_label from label_pairs_view WHERE label_pairs_view.parent_label = '{index_tuple[3]}'",
                "sqlite:///solvation.db",
            )
            
            # Check if solute data exists
            solute_dict = None
            if not math.isnan(solute_series.S[0]) if hasattr(solute_series, 'S') else True:
                solute_dict = dict(
                    S=solute_series.S[0] if hasattr(solute_series, 'S') else None,
                    B=solute_series.B[0] if hasattr(solute_series, 'B') else None,
                    E=solute_series.E[0] if hasattr(solute_series, 'E') else None,
                    L=solute_series.L[0] if hasattr(solute_series, 'L') else None,
                    A=solute_series.A[0] if hasattr(solute_series, 'A') else None,
                    V=solute_series.V[0] if hasattr(solute_series, 'V') else None,
                )
                # Remove None values
                solute_dict = {k: v for k, v in solute_dict.items() if v is not None}
            
            # Check if data count exists
            data_count_dict = None
            if hasattr(solute_series, 'S_count') and not math.isnan(solute_series.S_count[0]):
                data_count_dict = dict(
                    S=solute_series.S_count[0] if hasattr(solute_series, 'S_count') else None,
                    B=solute_series.B_count[0] if hasattr(solute_series, 'B_count') else None,
                    E=solute_series.E_count[0] if hasattr(solute_series, 'E_count') else None,
                    L=solute_series.L_count[0] if hasattr(solute_series, 'L_count') else None,
                    A=solute_series.A_count[0] if hasattr(solute_series, 'A_count') else None,
                )
                # Remove None values
                data_count_dict = {k: v for k, v in data_count_dict.items() if v is not None}
            
            formatted_dict = dict(
                # don't keep the internal database id in the text dump
                # id=row.id
                label=index_tuple[3],
                children=group_pairs["child_label"].to_list(),
                short_description=index_tuple[1],
                long_description=index_tuple[2],
                group=index_tuple[4],
            )
            
            if solute_dict:
                formatted_dict["solute"] = solute_dict
            
            if data_count_dict:
                formatted_dict["dataCount"] = data_count_dict
                
            all_rows.append(formatted_dict)

        with open(Path(f"yml/groups/{group_name}.yml"), "w") as f:
            yaml.dump_all(all_rows, f, yaml.SafeDumper, sort_keys=False)


# SQL should give the errors if data is improperly provided - just need to design triggers and
# ddl well enough and then pass them through in a sensible way here
def gen_db():
    # connect to the database
    engine = create_engine("sqlite:///solvation.db", echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    SCHEMA_BASE.metadata.create_all(engine)

    # initialize counters
    entry_counter = 0
    solute_data_counter = 0
    solvent_data_counter = 0
    data_count_counter = 0

    # load the libraries
    library_dir = Path("./yml/libraries")
    for library_file in tqdm(library_dir.glob("*"), desc="Loading libraries"):
        with open(library_file, "r") as f:
            all_rows = list(yaml.safe_load_all(f))
        for row in all_rows:
            # do the inverse mapping, use counters to rebuild the internal index
            if "solute" in row:
                new_row = SoluteLibrary(
                    id=entry_counter,
                    name=library_file.stem,
                    short_description=row["short_description"],
                    long_description=row["long_description"],
                    label=row["label"],
                    molecule=row["molecule"],
                )
                session.add(new_row)
                
                # Add solute data
                solute_dict = row["solute"]
                new_solute = SoluteData(
                    id=solute_data_counter,
                    parent_id=entry_counter,
                    S=solute_dict.get("S"),
                    B=solute_dict.get("B"),
                    E=solute_dict.get("E"),
                    L=solute_dict.get("L"),
                    A=solute_dict.get("A"),
                    V=solute_dict.get("V"),
                )
                session.add(new_solute)
                solute_data_counter += 1
                
            elif "solvent" in row:
                new_row = SolventLibrary(
                    id=entry_counter,
                    name=library_file.stem,
                    short_description=row["short_description"],
                    long_description=row["long_description"],
                    label=row["label"],
                    molecule=row["molecule"],
                )
                session.add(new_row)
                
                # Add solvent data
                solvent_dict = row["solvent"]
                new_solvent = SolventData(
                    id=solvent_data_counter,
                    parent_id=entry_counter,
                    s_g=solvent_dict.get("s_g"),
                    b_g=solvent_dict.get("b_g"),
                    e_g=solvent_dict.get("e_g"),
                    l_g=solvent_dict.get("l_g"),
                    a_g=solvent_dict.get("a_g"),
                    c_g=solvent_dict.get("c_g"),
                    s_h=solvent_dict.get("s_h"),
                    b_h=solvent_dict.get("b_h"),
                    e_h=solvent_dict.get("e_h"),
                    l_h=solvent_dict.get("l_h"),
                    a_h=solvent_dict.get("a_h"),
                    c_h=solvent_dict.get("c_h"),
                    A=solvent_dict.get("A"),
                    B=solvent_dict.get("B"),
                    C=solvent_dict.get("C"),
                    D=solvent_dict.get("D"),
                    E=solvent_dict.get("E"),
                    alpha=solvent_dict.get("alpha"),
                    beta=solvent_dict.get("beta"),
                    eps=solvent_dict.get("eps"),
                    name_in_coolprop=solvent_dict.get("name_in_coolprop"),
                )
                session.add(new_solvent)
                solvent_data_counter += 1
                
                # Add data count if present
                if "dataCount" in row:
                    data_count_dict = row["dataCount"]
                    new_data_count = DataCountSolvent(
                        id=data_count_counter,
                        parent_id=entry_counter,
                        dGsolvCount=data_count_dict.get("dGsolvCount"),
                        dGsolvMAE_value=data_count_dict.get("dGsolvMAE", [None, None])[0],
                        dGsolvMAE_unit=data_count_dict.get("dGsolvMAE", [None, None])[1],
                        dHsolvCount=data_count_dict.get("dHsolvCount"),
                        dHsolvMAE_value=data_count_dict.get("dHsolvMAE", [None, None])[0],
                        dHsolvMAE_unit=data_count_dict.get("dHsolvMAE", [None, None])[1],
                    )
                    session.add(new_data_count)
                    data_count_counter += 1
            else:
                # Fallback to generic solvation library
                new_row = SolvationLibraries(
                    id=entry_counter,
                    name=library_file.stem,
                    short_description=row["short_description"],
                    long_description=row["long_description"],
                    label=row["label"],
                    molecule=row["molecule"],
                )
                session.add(new_row)
                
            entry_counter += 1

    # more counters
    entry_count = 0
    group_solute_count = 0
    group_data_count_count = 0
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

            # Add solute data if present
            if "solute" in row:
                solute_dict = row["solute"]
                new_solute = SoluteData(
                    id=group_solute_count,
                    parent_id=entry_count,
                    S=solute_dict.get("S"),
                    B=solute_dict.get("B"),
                    E=solute_dict.get("E"),
                    L=solute_dict.get("L"),
                    A=solute_dict.get("A"),
                    V=solute_dict.get("V"),
                )
                session.add(new_solute)
                group_solute_count += 1
            
            # Add data count if present
            if "dataCount" in row:
                data_count_dict = row["dataCount"]
                new_data_count = DataCountGAV(
                    id=group_data_count_count,
                    parent_id=entry_count,
                    S=data_count_dict.get("S"),
                    B=data_count_dict.get("B"),
                    E=data_count_dict.get("E"),
                    L=data_count_dict.get("L"),
                    A=data_count_dict.get("A"),
                )
                session.add(new_data_count)
                group_data_count_count += 1
                
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

    session.execute(solvation_groups_view_sql)
    session.execute(solute_libraries_view_sql)
    session.execute(solvent_libraries_view_sql)
    session.execute(label_pairs_view_sql)

    session.close()


if __name__ == "__main__":
    dump_db()
    Path("solvation.db").rename("old.db")
    gen_db()
