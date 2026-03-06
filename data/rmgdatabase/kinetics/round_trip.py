import yaml
import ast
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

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

def format_kinetics(r):
    if pd.isna(r.type): return None
    k = {"type": r.type}
    if pd.notna(r.A_val): k["A"] = [r.A_val, r.A_unit]
    if pd.notna(r.n): k["n"] = r.n
    if pd.notna(r.Ea_val): k["Ea"] = [r.Ea_val, r.Ea_unit]
    if pd.notna(r.T0_val): k["T0"] = [r.T0_val, r.T0_unit]
    if pd.notna(r.w0_val): k["w0"] = [r.w0_val, r.w0_unit]
    if pd.notna(r.E0_val): k["E0"] = [r.E0_val, r.E0_unit]
    if pd.notna(r.Tmin_val): k["Tmin"] = [r.Tmin_val, r.Tmin_unit]
    if pd.notna(r.Tmax_val): k["Tmax"] = [r.Tmax_val, r.Tmax_unit]
    if pd.notna(r.comment) and r.comment: k["comment"] = r.comment
    return k

def dump_db():
    engine = create_engine("sqlite:///kinetics.db", echo=False)
    
    # Dump Libraries
    df_lib = pd.read_sql("SELECT * FROM kinetics_libraries_table", engine)
    for _, lib in df_lib.iterrows():
        name = lib["name"]
        ldir = Path(f"yml/libraries/{name}")
        ldir.mkdir(parents=True, exist_ok=True)
        
        with open(ldir / "meta.yml", "w") as f:
            yaml.dump(clean_dict({"short_description": lib.short_description, "long_description": lib.long_description}), f, sort_keys=False)
            
        df_dict = pd.read_sql(f"SELECT * FROM kinetics_library_dictionary_view WHERE library_name='{name}'", engine)
        if not df_dict.empty:
            dict_rows = [clean_dict({"label": r.label, "adjacency_list": r.adjacency_list}) for _, r in df_dict.iterrows()]
            with open(ldir / "dictionary.yml", "w") as f: yaml.dump_all(dict_rows, f, yaml.SafeDumper, sort_keys=False)
            
        df_reac = pd.read_sql(f"SELECT * FROM kinetics_library_reactions_view WHERE library_name='{name}'", engine)
        if not df_reac.empty:
            reac_rows = []
            for _, r in df_reac.iterrows():
                d = clean_dict({"label": r.label, "degeneracy": r.degeneracy, "short_description": r.short_description, "long_description": r.long_description, "rank": int(r["rank"]) if pd.notna(r["rank"]) else None})
                k = format_kinetics(r)
                if k: d["kinetics"] = k
                reac_rows.append(d)
            with open(ldir / "reactions.yml", "w") as f: yaml.dump_all(reac_rows, f, yaml.SafeDumper, sort_keys=False)
            
    # Dump Families
    df_fam = pd.read_sql("SELECT * FROM kinetics_families_view", engine)
    for _, fam in df_fam.iterrows():
        name = fam["name"]
        fdir = Path(f"yml/families/{name}")
        fdir.mkdir(parents=True, exist_ok=True)
        (fdir / "training").mkdir(parents=True, exist_ok=True)
        
        with open(fdir / "meta.yml", "w") as f:
            yaml.dump(clean_dict({
                "short_description": fam.short_description, 
                "long_description": fam.long_description, 
                "template": ast.literal_eval(fam.template) if pd.notna(fam.template) and fam.template else None,
                "recipe": ast.literal_eval(fam.recipe) if pd.notna(fam.recipe) and fam.recipe else None, 
                "reversible": bool(fam.reversible) if pd.notna(fam.reversible) else None, 
                "reverse_map": ast.literal_eval(fam.reverse_map) if pd.notna(fam.reverse_map) and fam.reverse_map else None,
                "reactant_num": int(fam.reactant_num) if pd.notna(fam.reactant_num) else None,
                "product_num": int(fam.product_num) if pd.notna(fam.product_num) else None,
                "auto_generated": bool(fam.auto_generated) if pd.notna(fam.auto_generated) else None
            }), f, sort_keys=False)
            
        df_groups = pd.read_sql(f"SELECT * FROM kinetics_family_groups_view WHERE family_name='{name}'", engine)
        if not df_groups.empty:
            group_rows = []
            for _, r in df_groups.iterrows():
                d = clean_dict({"label": r.label, "group": r.group_adj_list})
                ch = pd.read_sql(f"SELECT child_label FROM label_pairs_view WHERE parent_label='{r.label}'", engine)
                d["children"] = ch["child_label"].tolist() if not ch.empty else []
                group_rows.append(d)
            with open(fdir / "groups.yml", "w") as f: yaml.dump_all(group_rows, f, yaml.SafeDumper, sort_keys=False)
            
        df_rules = pd.read_sql(f"SELECT * FROM kinetics_family_rules_view WHERE family_name='{name}'", engine)
        if not df_rules.empty:
            rule_rows = []
            for _, r in df_rules.iterrows():
                d = clean_dict({"label": r.label, "short_description": r.short_description, "long_description": r.long_description, "rank": int(r["rank"]) if pd.notna(r["rank"]) else None})
                k = format_kinetics(r)
                if k: d["kinetics"] = k
                rule_rows.append(d)
            with open(fdir / "rules.yml", "w") as f: yaml.dump_all(rule_rows, f, yaml.SafeDumper, sort_keys=False)
            
        df_tdict = pd.read_sql(f"SELECT * FROM kinetics_family_training_dictionary_view WHERE family_name='{name}'", engine)
        if not df_tdict.empty:
            tdict_rows = [clean_dict({"label": r.label, "adjacency_list": r.adjacency_list}) for _, r in df_tdict.iterrows()]
            with open(fdir / "training/dictionary.yml", "w") as f: yaml.dump_all(tdict_rows, f, yaml.SafeDumper, sort_keys=False)
            
        df_treac = pd.read_sql(f"SELECT * FROM kinetics_family_training_reactions_view WHERE family_name='{name}'", engine)
        if not df_treac.empty:
            treac_rows = []
            for _, r in df_treac.iterrows():
                d = clean_dict({"label": r.label, "degeneracy": r.degeneracy, "short_description": r.short_description, "long_description": r.long_description, "rank": int(r["rank"]) if pd.notna(r["rank"]) else None})
                k = format_kinetics(r)
                if k: d["kinetics"] = k
                treac_rows.append(d)
            with open(fdir / "training/reactions.yml", "w") as f: yaml.dump_all(treac_rows, f, yaml.SafeDumper, sort_keys=False)

if __name__ == "__main__":
    dump_db()
