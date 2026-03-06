import yaml
import ast
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

from rmgdb.solvation.schema import SoluteData, SolventData, DataCountGAV, DataCountSolvent

yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str
repr_str = lambda dumper, data: dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|") if "\n" in data else dumper.org_represent_str(data)
yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)

def clean_dict(d):
    cleaned = {}
    for k, v in d.items():
        if v is None: continue
        if isinstance(v, float) and pd.isna(v): continue
        cleaned[k] = v
    return cleaned

def dump_db():
    for f in ["yml/libraries", "yml/groups"]: Path(f).mkdir(parents=True, exist_ok=True)
    engine = create_engine("sqlite:///solvation.db", echo=False)

    # 1. Solute Libraries
    df = pd.read_sql("SELECT * FROM solute_libraries_view", engine)
    if not df.empty:
        for name, grp in df.groupby("name"):
            rows = []
            for _, r in grp.iterrows():
                mol = r.molecule
                if isinstance(mol, str) and mol.startswith("["):
                    try:
                        mol = ast.literal_eval(mol)
                    except (ValueError, SyntaxError):
                        pass  # It's likely a SMILES string or adjacency list starting with '[', not a Python list
                        
                d = clean_dict({"label": r.label, "short_description": r.short_description, "long_description": r.long_description, "molecule": mol})
                if pd.notna(r.S):
                    d["solute"] = clean_dict({"S": r.S, "B": r.B, "E": r.E, "L": r.L, "A": r.A, "V": r.V})
                rows.append(d)
            if rows:
                with open(f"yml/libraries/{name}.yml", "w") as f: yaml.dump_all(rows, f, yaml.SafeDumper, sort_keys=False)

    # 2. Solvent Libraries
    df = pd.read_sql("SELECT * FROM solvent_libraries_view", engine)
    if not df.empty:
        for name, grp in df.groupby("name"):
            rows = []
            for _, r in grp.iterrows():
                mol = r.molecule
                if isinstance(mol, str) and mol.startswith("["):
                    try:
                        mol = ast.literal_eval(mol)
                    except (ValueError, SyntaxError):
                        pass

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

    # 3. Groups
    df = pd.read_sql("SELECT * FROM solute_groups_view", engine)
    if not df.empty:
        for name, grp in df.groupby("name"):
            rows = []
            for _, r in grp.iterrows():
                d = clean_dict({"label": r.label, "short_description": r.short_description, "long_description": r.long_description, "group": r.group})
                ch = pd.read_sql(f"SELECT child_label FROM label_pairs_view WHERE parent_label='{r.label}'", engine)
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

if __name__ == "__main__":
    dump_db()
