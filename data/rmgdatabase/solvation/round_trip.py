import yaml
import ast
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from rmgdb.solvation.schema import (
    SCHEMA_BASE, Groups, GroupsTree, SoluteLibraries, SolventLibraries, 
    SoluteData, SolventData, DataCountGAV, DataCountSolvent
)
from rmgdb.solvation.views import (
    label_pairs_view_sql, solute_libraries_view_sql, 
    solvent_libraries_view_sql, solute_groups_view_sql
)

yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str
repr_str = lambda dumper, data: dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|+") if "\n" in data else dumper.org_represent_str(data)
yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)
yaml.add_representer(np.float64, lambda dumper, data: dumper.represent_float(float(data)), Dumper=yaml.SafeDumper)
yaml.add_representer(np.float32, lambda dumper, data: dumper.represent_float(float(data)), Dumper=yaml.SafeDumper)
yaml.add_representer(np.int64, lambda dumper, data: dumper.represent_int(int(data)), Dumper=yaml.SafeDumper)
yaml.add_representer(np.int32, lambda dumper, data: dumper.represent_int(int(data)), Dumper=yaml.SafeDumper)

def clean_dict(d):
    cleaned = {}
    for k, v in d.items():
        if v is None: continue
        if isinstance(v, (float, np.floating)) and pd.isna(v): continue
        cleaned[k] = v
    return cleaned

def dump_db():
    for f in ["yml/libraries", "yml/groups"]: Path(f).mkdir(parents=True, exist_ok=True)
    engine = create_engine("sqlite:///solvation.db", echo=False)

    df_solute = pd.read_sql("SELECT * FROM solute_libraries_view ORDER BY id", engine)
    if not df_solute.empty:
        for name, grp in df_solute.groupby("name"):
            rows = []
            for _, r in grp.iterrows():
                mol = r.molecule
                if isinstance(mol, str) and mol.startswith("["):
                    try: mol = ast.literal_eval(mol)
                    except (ValueError, SyntaxError): pass
                d = clean_dict({"label": r.label, "short_description": r.short_description, "long_description": r.long_description, "molecule": mol})
                if pd.notna(r.S): d["solute"] = clean_dict({"S": r.S, "B": r.B, "E": r.E, "L": r.L, "A": r.A, "V": r.V})
                rows.append(d)
            if rows:
                with open(f"yml/libraries/{name}.yml", "w") as f: yaml.dump_all(rows, f, yaml.SafeDumper, sort_keys=False)

    df_solvent = pd.read_sql("SELECT * FROM solvent_libraries_view ORDER BY id", engine)
    if not df_solvent.empty:
        for name, grp in df_solvent.groupby("name"):
            rows = []
            for _, r in grp.iterrows():
                mol = r.molecule
                if isinstance(mol, str) and mol.startswith("["):
                    try: mol = ast.literal_eval(mol)
                    except (ValueError, SyntaxError): pass
                d = clean_dict({"label": r.label, "short_description": r.short_description, "long_description": r.long_description, "molecule": mol})
                if pd.notna(r.s_g):
                    d["solvent"] = clean_dict({
                        "s_g": r.s_g, "b_g": r.b_g, "e_g": r.e_g, "l_g": r.l_g, "a_g": r.a_g, "c_g": r.c_g,
                        "s_h": r.s_h, "b_h": r.b_h, "e_h": r.e_h, "l_h": r.l_h, "a_h": r.a_h, "c_h": r.c_h,
                        "A": r.A, "B": r.B, "C": r.C, "D": r.D, "E": r.E,
                        "alpha": r.alpha, "beta": r.beta, "eps": r.eps, "n": r.n, "name_in_coolprop": r.name_in_coolprop
                    })
                if pd.notna(r.dGsolvCount) or pd.notna(r.dHsolvCount):
                    dc = clean_dict({"dGsolvCount": int(r.dGsolvCount) if pd.notna(r.dGsolvCount) else None, "dHsolvCount": int(r.dHsolvCount) if pd.notna(r.dHsolvCount) else None})
                    if pd.notna(r.dGsolvMAE_val): dc["dGsolvMAE"] = [r.dGsolvMAE_val, r.dGsolvMAE_unit]
                    if pd.notna(r.dHsolvMAE_val): dc["dHsolvMAE"] = [r.dHsolvMAE_val, r.dHsolvMAE_unit]
                    d["dataCount"] = dc
                rows.append(d)
            if rows:
                with open(f"yml/libraries/{name}.yml", "w") as f: yaml.dump_all(rows, f, yaml.SafeDumper, sort_keys=False)

    df_groups = pd.read_sql("SELECT * FROM solute_groups_view ORDER BY id", engine)
    if not df_groups.empty:
        for name, grp in df_groups.groupby("name"):
            rows = []
            for _, r in grp.iterrows():
                d = clean_dict({"label": r.label, "short_description": r.short_description, "long_description": r.long_description, "group": r.group})
                
                # Filter specifically by the exact file (name) to block crossover
                ch = pd.read_sql(text("SELECT child_label FROM label_pairs_view WHERE parent_label=:lbl AND name=:name ORDER BY id"), engine, params={"lbl": r.label, "name": name})
                d["children"] = ch["child_label"].tolist() if not ch.empty else []
                
                if pd.notna(r.solute_pointer) and r.solute_pointer:
                    d["solute"] = r.solute_pointer
                elif pd.notna(r.solute_S):
                    d["solute"] = clean_dict({"S": r.solute_S, "B": r.solute_B, "E": r.solute_E, "L": r.solute_L, "A": r.solute_A, "V": r.solute_V})
                if pd.notna(r.count_S):
                    dc = {}
                    for k in ["S", "B", "E", "L", "A"]:
                        val = getattr(r, f"count_{k}")
                        if pd.notna(val): dc[k] = int(val)
                    d["dataCount"] = dc
                rows.append(d)
            if rows:
                with open(f"yml/groups/{name}.yml", "w") as f: yaml.dump_all(rows, f, yaml.SafeDumper, sort_keys=False)

def gen_db():
    engine = create_engine("sqlite:///solvation.db", echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    SCHEMA_BASE.metadata.create_all(engine)

    counts = {"group": 0, "solute_lib": 0, "solvent_lib": 0, "solute_data": 0, "solvent_data": 0, "count_gav": 0, "count_solvent": 0, "tree": 0}

    if Path("yml/libraries").exists():
        for f in sorted(Path("yml/libraries").glob("*.yml")):
            with open(f, "r") as fl:
                for row in yaml.safe_load_all(fl):
                    mol = repr(row["molecule"]) if isinstance(row.get("molecule"), list) else row.get("molecule", "")
                    
                    # Fix: Explicitly check file stem for solvents, since they may only have a dataCount
                    if f.stem == "solvent" or "solvent" in row:
                        session.add(SolventLibraries(id=counts["solvent_lib"], name=f.stem, label=row["label"], molecule=mol, short_description=row.get("short_description", ""), long_description=row.get("long_description", "")))
                        
                        if "solvent" in row:
                            sd = row["solvent"]
                            session.add(SolventData(id=counts["solvent_data"], solvent_library_parent_id=counts["solvent_lib"], **sd))
                            counts["solvent_data"] += 1
                        
                        if "dataCount" in row:
                            dc = row["dataCount"]
                            session.add(DataCountSolvent(
                                id=counts["count_solvent"], solvent_library_parent_id=counts["solvent_lib"],
                                dGsolvCount=dc.get("dGsolvCount"), dGsolvMAE_val=dc.get("dGsolvMAE", [None])[0], dGsolvMAE_unit=dc.get("dGsolvMAE", [None, None])[1] if dc.get("dGsolvMAE") else None,
                                dHsolvCount=dc.get("dHsolvCount"), dHsolvMAE_val=dc.get("dHsolvMAE", [None])[0], dHsolvMAE_unit=dc.get("dHsolvMAE", [None, None])[1] if dc.get("dHsolvMAE") else None
                            ))
                            counts["count_solvent"] += 1
                        counts["solvent_lib"] += 1
                    else:
                        session.add(SoluteLibraries(id=counts["solute_lib"], name=f.stem, label=row["label"], molecule=mol, short_description=row.get("short_description", ""), long_description=row.get("long_description", "")))
                        if "solute" in row and isinstance(row["solute"], dict):
                            session.add(SoluteData(id=counts["solute_data"], solute_library_parent_id=counts["solute_lib"], **row["solute"]))
                            counts["solute_data"] += 1
                        counts["solute_lib"] += 1

    if Path("yml/groups").exists():
        for f in sorted(Path("yml/groups").glob("*.yml")):
            # Tightly scoped dictionary per file
            label_to_id = {}
            with open(f, "r") as fl:
                all_rows = list(yaml.safe_load_all(fl))
                
                # First pass: Create entities and gather PK mappings
                for row in all_rows:
                    label_to_id[row["label"]] = counts["group"]
                    ptr = row["solute"] if isinstance(row.get("solute"), str) else None
                    session.add(Groups(id=counts["group"], name=f.stem, label=row["label"], group=row.get("group", ""), short_description=row.get("short_description", ""), long_description=row.get("long_description", ""), solute_pointer=ptr))
                    
                    if "solute" in row and isinstance(row["solute"], dict):
                        session.add(SoluteData(id=counts["solute_data"], group_parent_id=counts["group"], **row["solute"]))
                        counts["solute_data"] += 1
                    if "dataCount" in row:
                        session.add(DataCountGAV(id=counts["count_gav"], group_parent_id=counts["group"], **row["dataCount"]))
                        counts["count_gav"] += 1
                    counts["group"] += 1

                # Second pass: Build strictly linked tree relationships
                for row in all_rows:
                    for child in row.get("children", []):
                        if child in label_to_id:
                            session.add(GroupsTree(id=counts["tree"], parent_id=label_to_id[row["label"]], child_id=label_to_id[child]))
                            counts["tree"] += 1

    try:
        session.commit()
        session.execute(solute_groups_view_sql)
        session.execute(solute_libraries_view_sql)
        session.execute(solvent_libraries_view_sql)
        session.execute(label_pairs_view_sql)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error during gen_db commit: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    dump_db()
    Path("solvation.db").rename("old.db")
    gen_db()
