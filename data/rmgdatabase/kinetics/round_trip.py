import yaml
import ast
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine, text

# -- PyYAML Representers --

# Fix multiline string printing
yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str
repr_str = lambda dumper, data: dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|") if "\n" in data else dumper.org_represent_str(data)
yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)

# Teach PyYAML how to dump NumPy floats and ints returned by Pandas
yaml.add_representer(np.float64, lambda dumper, data: dumper.represent_float(float(data)), Dumper=yaml.SafeDumper)
yaml.add_representer(np.float32, lambda dumper, data: dumper.represent_float(float(data)), Dumper=yaml.SafeDumper)
yaml.add_representer(np.int64, lambda dumper, data: dumper.represent_int(int(data)), Dumper=yaml.SafeDumper)
yaml.add_representer(np.int32, lambda dumper, data: dumper.represent_int(int(data)), Dumper=yaml.SafeDumper)

# -------------------------

def clean_dict(d):
    cleaned = {}
    for k, v in d.items():
        if v is None: 
            continue
        # Only use pd.isna on scalar floats to prevent list array ambiguous truth value errors
        if isinstance(v, (float, np.floating)) and pd.isna(v): 
            continue
        cleaned[k] = v
    return cleaned

def pull_kinetics(fk_col, fk_id, engine):
    # Check Arrhenius / MultiArrhenius
    arrs = pd.read_sql(text(f"SELECT * FROM kinetics_arrhenius_table WHERE {fk_col} = :id"), engine, params={"id": fk_id})
    if not arrs.empty:
        multi = []
        for _, r in arrs.iterrows():
            d = clean_dict({"type": r.kinetics_type, "A": [r.A_val, r.A_unit] if pd.notna(r.A_val) else None, "n": r.n, "Ea": [r.Ea_val, r.Ea_unit] if pd.notna(r.Ea_val) else None, "T0": [r.T0_val, r.T0_unit] if pd.notna(r.T0_val) else None, "Tmin": [r.Tmin_val, r.Tmin_unit] if pd.notna(r.Tmin_val) else None, "Tmax": [r.Tmax_val, r.Tmax_unit] if pd.notna(r.Tmax_val) else None, "comment": r.comment})
            multi.append(clean_dict(d))
        if len(multi) > 1: return {"type": "MultiArrhenius", "arrhenius": multi}
        return multi[0]

    # Check ArrheniusEP
    ep = pd.read_sql(text(f"SELECT * FROM kinetics_arrhenius_ep_table WHERE {fk_col} = :id"), engine, params={"id": fk_id})
    if not ep.empty:
        r = ep.iloc[0]
        return clean_dict({"type": r.kinetics_type, "A": [r.A_val, r.A_unit] if pd.notna(r.A_val) else None, "n": r.n, "alpha": r.alpha, "E0": [r.E0_val, r.E0_unit] if pd.notna(r.E0_val) else None, "Tmin": [r.Tmin_val, r.Tmin_unit] if pd.notna(r.Tmin_val) else None, "Tmax": [r.Tmax_val, r.Tmax_unit] if pd.notna(r.Tmax_val) else None, "comment": r.comment})

    # Check ArrheniusBM
    bm = pd.read_sql(text(f"SELECT * FROM kinetics_arrhenius_bm_table WHERE {fk_col} = :id"), engine, params={"id": fk_id})
    if not bm.empty:
        r = bm.iloc[0]
        return clean_dict({"type": r.kinetics_type, "A": [r.A_val, r.A_unit] if pd.notna(r.A_val) else None, "n": r.n, "w0": [r.w0_val, r.w0_unit] if pd.notna(r.w0_val) else None, "E0": [r.E0_val, r.E0_unit] if pd.notna(r.E0_val) else None, "Tmin": [r.Tmin_val, r.Tmin_unit] if pd.notna(r.Tmin_val) else None, "Tmax": [r.Tmax_val, r.Tmax_unit] if pd.notna(r.Tmax_val) else None, "comment": r.comment})

    # Check Marcus
    marcus = pd.read_sql(text(f"SELECT * FROM kinetics_marcus_table WHERE {fk_col} = :id"), engine, params={"id": fk_id})
    if not marcus.empty:
        r = marcus.iloc[0]
        c_df = pd.read_sql(text(f"SELECT * FROM kinetics_marcus_coefs_table WHERE marcus_id = :id ORDER BY coef_index"), engine, params={"id": r.id})
        coefs = [float(x) for x in c_df["coeff_value"].tolist()] if not c_df.empty else None
        
        return clean_dict({
            "type": "Marcus",
            "A": [r.A_val, r.A_unit] if pd.notna(r.A_val) else None,
            "n": r.n,
            "lmbd_i_coefs": coefs,
            "beta": [r.beta_val, r.beta_unit] if pd.notna(r.beta_val) else None,
            "wr": [r.wr_val, r.wr_unit] if pd.notna(r.wr_val) else None,
            "wp": [r.wp_val, r.wp_unit] if pd.notna(r.wp_val) else None,
            "lmbd_o": [r.lmbd_o_val, r.lmbd_o_unit] if pd.notna(r.lmbd_o_val) else None,
            "comment": r.comment
        })

    # Load Efficiencies
    eff_df = pd.read_sql(text(f"SELECT * FROM kinetics_efficiencies_table WHERE {fk_col} = :id"), engine, params={"id": fk_id})
    effs = {r.species_label: float(r.efficiency) for _, r in eff_df.iterrows()} if not eff_df.empty else None

    # Check Troe
    troe = pd.read_sql(text(f"SELECT * FROM kinetics_troe_table WHERE {fk_col} = :id"), engine, params={"id": fk_id})
    if not troe.empty:
        r = troe.iloc[0]
        return clean_dict({
            "type": "Troe", "alpha": r.alpha, "T3": [r.T3_val, r.T3_unit] if pd.notna(r.T3_val) else None, "T1": [r.T1_val, r.T1_unit] if pd.notna(r.T1_val) else None, "T2": [r.T2_val, r.T2_unit] if pd.notna(r.T2_val) else None,
            "arrheniusHigh": clean_dict({"type": "Arrhenius", "A": [r.high_A_val, r.high_A_unit] if pd.notna(r.high_A_val) else None, "n": r.high_n, "Ea": [r.high_Ea_val, r.high_Ea_unit] if pd.notna(r.high_Ea_val) else None}),
            "arrheniusLow": clean_dict({"type": "Arrhenius", "A": [r.low_A_val, r.low_A_unit] if pd.notna(r.low_A_val) else None, "n": r.low_n, "Ea": [r.low_Ea_val, r.low_Ea_unit] if pd.notna(r.low_Ea_val) else None}),
            "efficiencies": effs, "comment": r.comment
        })

    # Check Lindemann
    lind = pd.read_sql(text(f"SELECT * FROM kinetics_lindemann_table WHERE {fk_col} = :id"), engine, params={"id": fk_id})
    if not lind.empty:
        r = lind.iloc[0]
        return clean_dict({
            "type": "Lindemann",
            "arrheniusHigh": clean_dict({"type": "Arrhenius", "A": [r.high_A_val, r.high_A_unit] if pd.notna(r.high_A_val) else None, "n": r.high_n, "Ea": [r.high_Ea_val, r.high_Ea_unit] if pd.notna(r.high_Ea_val) else None}),
            "arrheniusLow": clean_dict({"type": "Arrhenius", "A": [r.low_A_val, r.low_A_unit] if pd.notna(r.low_A_val) else None, "n": r.low_n, "Ea": [r.low_Ea_val, r.low_Ea_unit] if pd.notna(r.low_Ea_val) else None}),
            "efficiencies": effs, "comment": r.comment
        })

    # Check ThirdBody
    tb = pd.read_sql(text(f"SELECT * FROM kinetics_third_body_table WHERE {fk_col} = :id"), engine, params={"id": fk_id})
    if not tb.empty:
        r = tb.iloc[0]
        return clean_dict({
            "type": "ThirdBody", "efficiencies": effs, "comment": r.comment,
            "arrheniusLow": clean_dict({"type": "Arrhenius", "A": [r.low_A_val, r.low_A_unit] if pd.notna(r.low_A_val) else None, "n": r.low_n, "Ea": [r.low_Ea_val, r.low_Ea_unit] if pd.notna(r.low_Ea_val) else None})
        })

    # Check Chebyshev
    cheb = pd.read_sql(text(f"SELECT * FROM kinetics_chebyshev_table WHERE {fk_col} = :id"), engine, params={"id": fk_id})
    if not cheb.empty:
        r = cheb.iloc[0]
        c_df = pd.read_sql(text(f"SELECT * FROM kinetics_chebyshev_coeffs_table WHERE chebyshev_id = :id ORDER BY t_index, p_index"), engine, params={"id": r.id})
        matrix = []
        if not c_df.empty:
            for t_idx in range(int(r.degreeT)):
                matrix.append([float(x) for x in c_df[c_df.t_index == t_idx]["coeff_value"].tolist()])
        return clean_dict({"type": "Chebyshev", "Tmin": [r.Tmin_val, r.Tmin_unit] if pd.notna(r.Tmin_val) else None, "Tmax": [r.Tmax_val, r.Tmax_unit] if pd.notna(r.Tmax_val) else None, "Pmin": [r.Pmin_val, r.Pmin_unit] if pd.notna(r.Pmin_val) else None, "Pmax": [r.Pmax_val, r.Pmax_unit] if pd.notna(r.Pmax_val) else None, "degreeT": int(r.degreeT) if pd.notna(r.degreeT) else None, "degreeP": int(r.degreeP) if pd.notna(r.degreeP) else None, "coeffs": matrix, "comment": r.comment})

    # Check PDepArrhenius / MultiPDepArrhenius
    pdep = pd.read_sql(text(f"SELECT * FROM kinetics_pdep_arrhenius_table WHERE {fk_col} = :id"), engine, params={"id": fk_id})
    if not pdep.empty:
        all_pdeps = []
        for _, r in pdep.iterrows():
            p_df = pd.read_sql(text(f"SELECT * FROM kinetics_pdep_arrhenius_pressures_table WHERE pdep_id = :id ORDER BY P_val"), engine, params={"id": r.id})
            pressures = [float(x) for x in p_df["P_val"].tolist()]
            p_unit = p_df["P_unit"].iloc[0] if not p_df.empty else None
            arrs = []
            for _, pr in p_df.iterrows():
                arrs.append(clean_dict({"type": "Arrhenius", "A": [pr.A_val, pr.A_unit] if pd.notna(pr.A_val) else None, "n": pr.n, "Ea": [pr.Ea_val, pr.Ea_unit] if pd.notna(pr.Ea_val) else None}))
            
            all_pdeps.append(clean_dict({"type": "PDepArrhenius", "Tmin": [r.Tmin_val, r.Tmin_unit] if pd.notna(r.Tmin_val) else None, "Tmax": [r.Tmax_val, r.Tmax_unit] if pd.notna(r.Tmax_val) else None, "pressures": [pressures, p_unit] if pressures else None, "arrhenius": arrs, "comment": r.comment}))
        if len(all_pdeps) > 1: return {"type": "MultiPDepArrhenius", "arrhenius": all_pdeps}
        return all_pdeps[0]

    # Check SoluteTSDiffData (wrapped in KineticsModel)
    solute_diff = pd.read_sql(text(f"SELECT * FROM kinetics_solute_ts_diff_table WHERE {fk_col} = :id"), engine, params={"id": fk_id})
    if not solute_diff.empty:
        r = solute_diff.iloc[0]
        ts_data = clean_dict({
            "type": "SoluteTSDiffData",
            "S_g": r.S_g, "B_g": r.B_g, "E_g": r.E_g, "L_g": r.L_g, "A_g": r.A_g, "K_g": r.K_g,
            "S_h": r.S_h, "B_h": r.B_h, "E_h": r.E_h, "L_h": r.L_h, "A_h": r.A_h, "K_h": r.K_h
        })
        return clean_dict({
            "type": "KineticsModel",
            "Tmin": [r.Tmin_val, r.Tmin_unit] if pd.notna(r.Tmin_val) else None, "Tmax": [r.Tmax_val, r.Tmax_unit] if pd.notna(r.Tmax_val) else None,
            "Pmin": [r.Pmin_val, r.Pmin_unit] if pd.notna(r.Pmin_val) else None, "Pmax": [r.Pmax_val, r.Pmax_unit] if pd.notna(r.Pmax_val) else None,
            "solute": ts_data, "comment": r.comment
        })

    return None

def dump_reaction_row(r, fk_col, fk_id, engine):
    d = {"label": r.label}
    if pd.notna(r.degeneracy): d["degeneracy"] = float(r.degeneracy)
    if r.short_description: d["short_description"] = r.short_description
    if r.long_description: d["long_description"] = r.long_description
    if pd.notna(r["rank"]): d["rank"] = int(r["rank"])
    if pd.notna(r.allow_max_rate_violation): d["allow_max_rate_violation"] = bool(r.allow_max_rate_violation)
    if pd.notna(r.reversible): d["reversible"] = bool(r.reversible)
    if pd.notna(r.elementary_high_p): d["elementary_high_p"] = bool(r.elementary_high_p)
    if pd.notna(r.duplicate): d["duplicate"] = bool(r.duplicate)
    
    k = pull_kinetics(fk_col, fk_id, engine)
    if k: d["kinetics"] = k
    return d

def dump_db():
    engine = create_engine("sqlite:///kinetics.db", echo=False)
    
    # Libraries
    df_lib = pd.read_sql("SELECT * FROM kinetics_libraries_table", engine)
    for _, lib in df_lib.iterrows():
        name = lib["name"]
        ldir = Path(f"yml/libraries/{name}"); ldir.mkdir(parents=True, exist_ok=True)
        with open(ldir / "meta.yml", "w") as f: yaml.dump(clean_dict({"short_description": lib.short_description, "long_description": lib.long_description}), f, sort_keys=False)
            
        df_dict = pd.read_sql(text("SELECT * FROM kinetics_library_dictionary_view WHERE library_name=:n"), engine, params={"n": name})
        if not df_dict.empty:
            dict_rows = [clean_dict({"label": r.label, "adjacency_list": r.adjacency_list}) for _, r in df_dict.iterrows()]
            with open(ldir / "dictionary.yml", "w") as f: yaml.dump_all(dict_rows, f, yaml.SafeDumper, sort_keys=False)
            
        df_reac = pd.read_sql(text("SELECT * FROM kinetics_library_reactions_table WHERE library_id=:id"), engine, params={"id": lib.id})
        if not df_reac.empty:
            reac_rows = [dump_reaction_row(r, "library_reaction_id", r.id, engine) for _, r in df_reac.iterrows()]
            with open(ldir / "reactions.yml", "w") as f: yaml.dump_all(reac_rows, f, yaml.SafeDumper, sort_keys=False)
            
    # Families
    df_fam = pd.read_sql("SELECT * FROM kinetics_families_view", engine)
    for _, fam in df_fam.iterrows():
        name = fam["name"]
        fdir = Path(f"yml/families/{name}"); fdir.mkdir(parents=True, exist_ok=True); (fdir / "training").mkdir(parents=True, exist_ok=True)
        
        meta = {"short_description": fam.short_description, "long_description": fam.long_description}
        if pd.notna(fam.template) and fam.template: meta["template"] = ast.literal_eval(fam.template)
        if pd.notna(fam.recipe) and fam.recipe: meta["recipe"] = ast.literal_eval(fam.recipe)
        if pd.notna(fam.reversible): meta["reversible"] = bool(fam.reversible)
        if pd.notna(fam.reverse_map) and fam.reverse_map: meta["reverse_map"] = ast.literal_eval(fam.reverse_map)
        if pd.notna(fam.reactant_num): meta["reactant_num"] = int(fam.reactant_num)
        if pd.notna(fam.product_num): meta["product_num"] = int(fam.product_num)
        if pd.notna(fam.auto_generated): meta["auto_generated"] = bool(fam.auto_generated)
        with open(fdir / "meta.yml", "w") as f: yaml.dump(clean_dict(meta), f, sort_keys=False)
            
        df_groups = pd.read_sql(text("SELECT * FROM kinetics_family_groups_view WHERE family_name=:n"), engine, params={"n": name})
        df_forbidden = pd.read_sql(text("SELECT * FROM kinetics_family_forbidden_groups_view WHERE family_name=:n"), engine, params={"n": name})
        
        group_rows = []
        if not df_groups.empty:
            for _, r in df_groups.iterrows():
                d = clean_dict({"label": r.label, "group": r.group_adj_list, "short_description": r.short_description, "long_description": r.long_description})
                ch = pd.read_sql(text("SELECT child_label FROM label_pairs_view WHERE parent_label=:lbl"), engine, params={"lbl": r.label})
                d["children"] = ch["child_label"].tolist() if not ch.empty else []
                group_rows.append(d)
                
        if not df_forbidden.empty:
            for _, r in df_forbidden.iterrows():
                d = clean_dict({"label": r.label, "group": r.group_adj_list, "forbidden": True, "short_description": r.short_description, "long_description": r.long_description})
                group_rows.append(d)
                
        if group_rows:
            with open(fdir / "groups.yml", "w") as f: yaml.dump_all(group_rows, f, yaml.SafeDumper, sort_keys=False)
            
        fid = pd.read_sql(text("SELECT id FROM kinetics_families_table WHERE name=:n"), engine, params={"n": name}).iloc[0].id
        df_rules = pd.read_sql(text("SELECT * FROM kinetics_family_rules_table WHERE family_id=:id"), engine, params={"id": fid})
        if not df_rules.empty:
            rule_rows = [dump_reaction_row(r, "family_rule_id", r.id, engine) for _, r in df_rules.iterrows()]
            with open(fdir / "rules.yml", "w") as f: yaml.dump_all(rule_rows, f, yaml.SafeDumper, sort_keys=False)
            
        df_tdict = pd.read_sql(text("SELECT * FROM kinetics_family_training_dictionary_view WHERE family_name=:n"), engine, params={"n": name})
        if not df_tdict.empty:
            tdict_rows = [clean_dict({"label": r.label, "adjacency_list": r.adjacency_list}) for _, r in df_tdict.iterrows()]
            with open(fdir / "training/dictionary.yml", "w") as f: yaml.dump_all(tdict_rows, f, yaml.SafeDumper, sort_keys=False)
            
        df_treac = pd.read_sql(text("SELECT * FROM kinetics_family_training_reactions_table WHERE family_id=:id"), engine, params={"id": fid})
        if not df_treac.empty:
            treac_rows = [dump_reaction_row(r, "family_training_reaction_id", r.id, engine) for _, r in df_treac.iterrows()]
            with open(fdir / "training/reactions.yml", "w") as f: yaml.dump_all(treac_rows, f, yaml.SafeDumper, sort_keys=False)

if __name__ == "__main__":
    dump_db()
