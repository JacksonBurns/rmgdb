import yaml
import ast
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from rmgdb.kinetics.schema import (
    SCHEMA_BASE, KineticsLibraries, KineticsLibraryDictionary, KineticsLibraryReactions, KineticsLibraryReactionSpecies,
    KineticsFamilies, KineticsFamilyGroups, KineticsFamilyForbiddenGroups, KineticsFamilyGroupsTree, KineticsFamilyRules,
    KineticsFamilyTrainingDictionary, KineticsFamilyTrainingReactions, KineticsFamilyTrainingReactionSpecies,
    KineticsArrhenius, KineticsArrheniusEP, KineticsArrheniusBM, KineticsMarcus, KineticsMarcusCoefs, 
    KineticsTroe, KineticsLindemann, KineticsThirdBody, KineticsEfficiencies, KineticsChebyshev, KineticsChebyshevCoeffs,
    KineticsPDepArrhenius, KineticsPDepArrheniusPressures, KineticsSoluteTSDiff
)
from rmgdb.kinetics.views import (
    label_pairs_view_sql, kinetics_library_reaction_species_view_sql, kinetics_family_training_reaction_species_view_sql,
    all_library_kinetics_view_sql, all_family_rules_kinetics_view_sql, all_family_training_kinetics_view_sql, 
    kinetics_library_dictionary_view_sql, kinetics_family_groups_view_sql, kinetics_family_forbidden_groups_view_sql, 
    kinetics_family_training_dictionary_view_sql, kinetics_families_view_sql
)

# Crucial fix to make PyYAML retain exact whitespace/newlines using `|+` syntax for long descriptions/adj_lists
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

def to_float(val):
    if val is None: return None
    try: return float(val)
    except (TypeError, ValueError): return None

def unpack_val_unit(lst):
    if not lst: return None, None
    if isinstance(lst, (float, int)): return float(lst), None
    return float(lst[0]), (lst[1] if len(lst) > 1 else None)

def parse_reaction_label(label):
    if '<=>' in label: r, p = label.split('<=>')
    elif '=>' in label: r, p = label.split('=>')
    elif '=' in label: r, p = label.split('=')
    else: return [], []
    return [x.strip() for x in r.split('+') if x.strip()], [x.strip() for x in p.split('+') if x.strip()]


# --------------------------------------------------------------------------------------
# EXPORT TO YAML (DUMP)
# --------------------------------------------------------------------------------------
def pull_kinetics(fk_col, fk_id, engine):
    arrs = pd.read_sql(text(f"SELECT * FROM kinetics_arrhenius_table WHERE {fk_col} = :id ORDER BY id"), engine, params={"id": fk_id})
    if not arrs.empty:
        multi = []
        for _, r in arrs.iterrows():
            multi.append(clean_dict({"type": r.kinetics_type, "A": [r.A_val, r.A_unit] if pd.notna(r.A_val) else None, "n": r.n, "Ea": [r.Ea_val, r.Ea_unit] if pd.notna(r.Ea_val) else None, "T0": [r.T0_val, r.T0_unit] if pd.notna(r.T0_val) else None, "Tmin": [r.Tmin_val, r.Tmin_unit] if pd.notna(r.Tmin_val) else None, "Tmax": [r.Tmax_val, r.Tmax_unit] if pd.notna(r.Tmax_val) else None, "comment": r.comment}))
        if len(multi) > 1: return {"type": "MultiArrhenius", "arrhenius": multi}
        return multi[0]

    ep = pd.read_sql(text(f"SELECT * FROM kinetics_arrhenius_ep_table WHERE {fk_col} = :id ORDER BY id"), engine, params={"id": fk_id})
    if not ep.empty:
        r = ep.iloc[0]
        return clean_dict({"type": r.kinetics_type, "A": [r.A_val, r.A_unit] if pd.notna(r.A_val) else None, "n": r.n, "alpha": r.alpha, "E0": [r.E0_val, r.E0_unit] if pd.notna(r.E0_val) else None, "Tmin": [r.Tmin_val, r.Tmin_unit] if pd.notna(r.Tmin_val) else None, "Tmax": [r.Tmax_val, r.Tmax_unit] if pd.notna(r.Tmax_val) else None, "comment": r.comment})

    bm = pd.read_sql(text(f"SELECT * FROM kinetics_arrhenius_bm_table WHERE {fk_col} = :id ORDER BY id"), engine, params={"id": fk_id})
    if not bm.empty:
        r = bm.iloc[0]
        return clean_dict({"type": r.kinetics_type, "A": [r.A_val, r.A_unit] if pd.notna(r.A_val) else None, "n": r.n, "w0": [r.w0_val, r.w0_unit] if pd.notna(r.w0_val) else None, "E0": [r.E0_val, r.E0_unit] if pd.notna(r.E0_val) else None, "Tmin": [r.Tmin_val, r.Tmin_unit] if pd.notna(r.Tmin_val) else None, "Tmax": [r.Tmax_val, r.Tmax_unit] if pd.notna(r.Tmax_val) else None, "comment": r.comment})

    marcus = pd.read_sql(text(f"SELECT * FROM kinetics_marcus_table WHERE {fk_col} = :id ORDER BY id"), engine, params={"id": fk_id})
    if not marcus.empty:
        r = marcus.iloc[0]
        c_df = pd.read_sql(text(f"SELECT * FROM kinetics_marcus_coefs_table WHERE marcus_id = :id ORDER BY coef_index"), engine, params={"id": r.id})
        coefs = [float(x) for x in c_df["coeff_value"].tolist()] if not c_df.empty else None
        return clean_dict({"type": "Marcus", "A": [r.A_val, r.A_unit] if pd.notna(r.A_val) else None, "n": r.n, "lmbd_i_coefs": coefs, "beta": [r.beta_val, r.beta_unit] if pd.notna(r.beta_val) else None, "wr": [r.wr_val, r.wr_unit] if pd.notna(r.wr_val) else None, "wp": [r.wp_val, r.wp_unit] if pd.notna(r.wp_val) else None, "lmbd_o": [r.lmbd_o_val, r.lmbd_o_unit] if pd.notna(r.lmbd_o_val) else None, "comment": r.comment})

    eff_df = pd.read_sql(text(f"SELECT * FROM kinetics_efficiencies_table WHERE {fk_col} = :id ORDER BY id"), engine, params={"id": fk_id})
    effs = {r.species_label: float(r.efficiency) for _, r in eff_df.iterrows()} if not eff_df.empty else None

    troe = pd.read_sql(text(f"SELECT * FROM kinetics_troe_table WHERE {fk_col} = :id ORDER BY id"), engine, params={"id": fk_id})
    if not troe.empty:
        r = troe.iloc[0]
        return clean_dict({"type": "Troe", "alpha": r.alpha, "T3": [r.T3_val, r.T3_unit] if pd.notna(r.T3_val) else None, "T1": [r.T1_val, r.T1_unit] if pd.notna(r.T1_val) else None, "T2": [r.T2_val, r.T2_unit] if pd.notna(r.T2_val) else None, "arrheniusHigh": clean_dict({"type": "Arrhenius", "A": [r.high_A_val, r.high_A_unit] if pd.notna(r.high_A_val) else None, "n": r.high_n, "Ea": [r.high_Ea_val, r.high_Ea_unit] if pd.notna(r.high_Ea_val) else None}), "arrheniusLow": clean_dict({"type": "Arrhenius", "A": [r.low_A_val, r.low_A_unit] if pd.notna(r.low_A_val) else None, "n": r.low_n, "Ea": [r.low_Ea_val, r.low_Ea_unit] if pd.notna(r.low_Ea_val) else None}), "efficiencies": effs, "comment": r.comment})

    lind = pd.read_sql(text(f"SELECT * FROM kinetics_lindemann_table WHERE {fk_col} = :id ORDER BY id"), engine, params={"id": fk_id})
    if not lind.empty:
        r = lind.iloc[0]
        return clean_dict({"type": "Lindemann", "arrheniusHigh": clean_dict({"type": "Arrhenius", "A": [r.high_A_val, r.high_A_unit] if pd.notna(r.high_A_val) else None, "n": r.high_n, "Ea": [r.high_Ea_val, r.high_Ea_unit] if pd.notna(r.high_Ea_val) else None}), "arrheniusLow": clean_dict({"type": "Arrhenius", "A": [r.low_A_val, r.low_A_unit] if pd.notna(r.low_A_val) else None, "n": r.low_n, "Ea": [r.low_Ea_val, r.low_Ea_unit] if pd.notna(r.low_Ea_val) else None}), "efficiencies": effs, "comment": r.comment})

    tb = pd.read_sql(text(f"SELECT * FROM kinetics_third_body_table WHERE {fk_col} = :id ORDER BY id"), engine, params={"id": fk_id})
    if not tb.empty:
        r = tb.iloc[0]
        return clean_dict({"type": "ThirdBody", "efficiencies": effs, "comment": r.comment, "arrheniusLow": clean_dict({"type": "Arrhenius", "A": [r.low_A_val, r.low_A_unit] if pd.notna(r.low_A_val) else None, "n": r.low_n, "Ea": [r.low_Ea_val, r.low_Ea_unit] if pd.notna(r.low_Ea_val) else None})})

    cheb = pd.read_sql(text(f"SELECT * FROM kinetics_chebyshev_table WHERE {fk_col} = :id ORDER BY id"), engine, params={"id": fk_id})
    if not cheb.empty:
        r = cheb.iloc[0]
        c_df = pd.read_sql(text(f"SELECT * FROM kinetics_chebyshev_coeffs_table WHERE chebyshev_id = :id ORDER BY t_index, p_index"), engine, params={"id": r.id})
        matrix = []
        if not c_df.empty:
            for t_idx in range(int(r.degreeT)):
                matrix.append([float(x) for x in c_df[c_df.t_index == t_idx]["coeff_value"].tolist()])
        return clean_dict({"type": "Chebyshev", "Tmin": [r.Tmin_val, r.Tmin_unit] if pd.notna(r.Tmin_val) else None, "Tmax": [r.Tmax_val, r.Tmax_unit] if pd.notna(r.Tmax_val) else None, "Pmin": [r.Pmin_val, r.Pmin_unit] if pd.notna(r.Pmin_val) else None, "Pmax": [r.Pmax_val, r.Pmax_unit] if pd.notna(r.Pmax_val) else None, "degreeT": int(r.degreeT) if pd.notna(r.degreeT) else None, "degreeP": int(r.degreeP) if pd.notna(r.degreeP) else None, "coeffs": matrix, "comment": r.comment})

    pdep = pd.read_sql(text(f"SELECT * FROM kinetics_pdep_arrhenius_table WHERE {fk_col} = :id ORDER BY id"), engine, params={"id": fk_id})
    if not pdep.empty:
        all_pdeps = []
        for _, r in pdep.iterrows():
            p_df = pd.read_sql(text(f"SELECT * FROM kinetics_pdep_arrhenius_pressures_table WHERE pdep_id = :id ORDER BY P_val, id"), engine, params={"id": r.id})
            pressures = [float(x) for x in p_df["P_val"].tolist()]
            p_unit = p_df["P_unit"].iloc[0] if not p_df.empty else None
            arrs = []
            for _, pr in p_df.iterrows():
                arrs.append(clean_dict({"type": "Arrhenius", "A": [pr.A_val, pr.A_unit] if pd.notna(pr.A_val) else None, "n": pr.n, "Ea": [pr.Ea_val, pr.Ea_unit] if pd.notna(pr.Ea_val) else None}))
            all_pdeps.append(clean_dict({"type": "PDepArrhenius", "Tmin": [r.Tmin_val, r.Tmin_unit] if pd.notna(r.Tmin_val) else None, "Tmax": [r.Tmax_val, r.Tmax_unit] if pd.notna(r.Tmax_val) else None, "pressures": [pressures, p_unit] if pressures else None, "arrhenius": arrs, "comment": r.comment}))
        if len(all_pdeps) > 1: return {"type": "MultiPDepArrhenius", "arrhenius": all_pdeps}
        return all_pdeps[0]

    solute_diff = pd.read_sql(text(f"SELECT * FROM kinetics_solute_ts_diff_table WHERE {fk_col} = :id ORDER BY id"), engine, params={"id": fk_id})
    if not solute_diff.empty:
        r = solute_diff.iloc[0]
        ts_data = clean_dict({"type": "SoluteTSDiffData", "S_g": r.S_g, "B_g": r.B_g, "E_g": r.E_g, "L_g": r.L_g, "A_g": r.A_g, "K_g": r.K_g, "S_h": r.S_h, "B_h": r.B_h, "E_h": r.E_h, "L_h": r.L_h, "A_h": r.A_h, "K_h": r.K_h})
        return clean_dict({"type": "KineticsModel", "Tmin": [r.Tmin_val, r.Tmin_unit] if pd.notna(r.Tmin_val) else None, "Tmax": [r.Tmax_val, r.Tmax_unit] if pd.notna(r.Tmax_val) else None, "Pmin": [r.Pmin_val, r.Pmin_unit] if pd.notna(r.Pmin_val) else None, "Pmax": [r.Pmax_val, r.Pmax_unit] if pd.notna(r.Pmax_val) else None, "solute": ts_data, "comment": r.comment})
    return None

def dump_reaction_row(r, fk_col, fk_id, engine):
    d = {"label": r.label}
    if pd.notna(r.degeneracy): d["degeneracy"] = float(r.degeneracy)
    if pd.notna(r.short_description) and r.short_description: d["short_description"] = r.short_description
    if pd.notna(r.long_description) and r.long_description: d["long_description"] = r.long_description
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
    
    df_lib = pd.read_sql("SELECT * FROM kinetics_libraries_table ORDER BY id", engine)
    for _, lib in df_lib.iterrows():
        name = lib["name"]
        ldir = Path(f"yml/libraries/{name}"); ldir.mkdir(parents=True, exist_ok=True)
        with open(ldir / "meta.yml", "w") as f: yaml.dump(clean_dict({"short_description": lib.short_description, "long_description": lib.long_description}), f, sort_keys=False)
            
        df_dict = pd.read_sql(text("SELECT * FROM kinetics_library_dictionary_view WHERE library_name=:n ORDER BY id"), engine, params={"n": name})
        if not df_dict.empty:
            dict_rows = [clean_dict({"label": r.label, "adjacency_list": r.adjacency_list}) for _, r in df_dict.iterrows()]
            with open(ldir / "dictionary.yml", "w") as f: yaml.dump_all(dict_rows, f, yaml.SafeDumper, sort_keys=False)
            
        df_reac = pd.read_sql(text("SELECT * FROM kinetics_library_reactions_table WHERE library_id=:id ORDER BY id"), engine, params={"id": lib.id})
        if not df_reac.empty:
            reac_rows = [dump_reaction_row(r, "library_reaction_id", r.id, engine) for _, r in df_reac.iterrows()]
            with open(ldir / "reactions.yml", "w") as f: yaml.dump_all(reac_rows, f, yaml.SafeDumper, sort_keys=False)
            
    df_fam = pd.read_sql("SELECT * FROM kinetics_families_view ORDER BY id", engine)
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
            
        df_groups = pd.read_sql(text("SELECT * FROM kinetics_family_groups_view WHERE family_name=:n ORDER BY id"), engine, params={"n": name})
        df_forbidden = pd.read_sql(text("SELECT * FROM kinetics_family_forbidden_groups_view WHERE family_name=:n ORDER BY id"), engine, params={"n": name})
        
        group_rows = []
        if not df_groups.empty:
            for _, r in df_groups.iterrows():
                d = clean_dict({"label": r.label, "group": r.group_adj_list, "short_description": r.short_description, "long_description": r.long_description})
                ch = pd.read_sql(text("SELECT child_label FROM label_pairs_view WHERE parent_label=:lbl ORDER BY id"), engine, params={"lbl": r.label})
                d["children"] = ch["child_label"].tolist() if not ch.empty else []
                group_rows.append(d)
                
        if not df_forbidden.empty:
            for _, r in df_forbidden.iterrows():
                d = clean_dict({"label": r.label, "group": r.group_adj_list, "forbidden": True, "short_description": r.short_description, "long_description": r.long_description})
                group_rows.append(d)
                
        if group_rows:
            with open(fdir / "groups.yml", "w") as f: yaml.dump_all(group_rows, f, yaml.SafeDumper, sort_keys=False)
            
        fid = pd.read_sql(text("SELECT id FROM kinetics_families_table WHERE name=:n ORDER BY id"), engine, params={"n": name}).iloc[0].id
        df_rules = pd.read_sql(text("SELECT * FROM kinetics_family_rules_table WHERE family_id=:id ORDER BY id"), engine, params={"id": fid})
        if not df_rules.empty:
            rule_rows = [dump_reaction_row(r, "family_rule_id", r.id, engine) for _, r in df_rules.iterrows()]
            with open(fdir / "rules.yml", "w") as f: yaml.dump_all(rule_rows, f, yaml.SafeDumper, sort_keys=False)
            
        df_tdict = pd.read_sql(text("SELECT * FROM kinetics_family_training_dictionary_view WHERE family_name=:n ORDER BY id"), engine, params={"n": name})
        if not df_tdict.empty:
            tdict_rows = [clean_dict({"label": r.label, "adjacency_list": r.adjacency_list}) for _, r in df_tdict.iterrows()]
            with open(fdir / "training/dictionary.yml", "w") as f: yaml.dump_all(tdict_rows, f, yaml.SafeDumper, sort_keys=False)
            
        df_treac = pd.read_sql(text("SELECT * FROM kinetics_family_training_reactions_table WHERE family_id=:id ORDER BY id"), engine, params={"id": fid})
        if not df_treac.empty:
            treac_rows = [dump_reaction_row(r, "family_training_reaction_id", r.id, engine) for _, r in df_treac.iterrows()]
            with open(fdir / "training/reactions.yml", "w") as f: yaml.dump_all(treac_rows, f, yaml.SafeDumper, sort_keys=False)


# --------------------------------------------------------------------------------------
# IMPORT FROM YAML (GEN)
# --------------------------------------------------------------------------------------
def insert_kinetics(k_dict, fk_col, fk_id, session, counts):
    if not k_dict: return
    ktype = k_dict.get("type")

    def ext(d):
        A_v, A_u = unpack_val_unit(d.get("A"))
        Ea_v, Ea_u = unpack_val_unit(d.get("Ea"))
        T0_v, T0_u = unpack_val_unit(d.get("T0"))
        Tmin_v, Tmin_u = unpack_val_unit(d.get("Tmin"))
        Tmax_v, Tmax_u = unpack_val_unit(d.get("Tmax"))
        return A_v, A_u, to_float(d.get("n")), Ea_v, Ea_u, T0_v, T0_u, Tmin_v, Tmin_u, Tmax_v, Tmax_u

    if ktype in ["Arrhenius", "SurfaceArrhenius", "StickingCoefficient", "ArrheniusChargeTransfer", "SurfaceChargeTransfer"]:
        Av, Au, nv, Eav, Eau, T0v, T0u, Tminv, Tminu, Tmaxv, Tmaxu = ext(k_dict)
        row = KineticsArrhenius(id=counts["k_arr"], kinetics_type=ktype, A_val=Av, A_unit=Au, n=nv, Ea_val=Eav, Ea_unit=Eau, T0_val=T0v, T0_unit=T0u, Tmin_val=Tminv, Tmin_unit=Tminu, Tmax_val=Tmaxv, Tmax_unit=Tmaxu, comment=k_dict.get("comment"))
        setattr(row, fk_col, fk_id); session.add(row); counts["k_arr"] += 1

    elif ktype == "MultiArrhenius":
        for arr in k_dict.get("arrhenius", []):
            if isinstance(arr, dict): insert_kinetics(arr, fk_col, fk_id, session, counts)

    elif ktype == "MultiPDepArrhenius":
        for arr in k_dict.get("arrhenius", []):
            if isinstance(arr, dict): insert_kinetics(arr, fk_col, fk_id, session, counts)

    elif ktype in ["ArrheniusEP", "SurfaceArrheniusBEP", "StickingCoefficientBEP"]:
        Av, Au, nv, _, _, _, _, Tminv, Tminu, Tmaxv, Tmaxu = ext(k_dict)
        E0v, E0u = unpack_val_unit(k_dict.get("E0"))
        row = KineticsArrheniusEP(id=counts["k_arrep"], kinetics_type=ktype, A_val=Av, A_unit=Au, n=nv, alpha=to_float(k_dict.get("alpha")), E0_val=E0v, E0_unit=E0u, Tmin_val=Tminv, Tmin_unit=Tminu, Tmax_val=Tmaxv, Tmax_unit=Tmaxu, comment=k_dict.get("comment"))
        setattr(row, fk_col, fk_id); session.add(row); counts["k_arrep"] += 1

    elif ktype in ["ArrheniusBM", "ArrheniusChargeTransferBM"]:
        Av, Au, nv, _, _, _, _, Tminv, Tminu, Tmaxv, Tmaxu = ext(k_dict)
        w0v, w0u = unpack_val_unit(k_dict.get("w0")); E0v, E0u = unpack_val_unit(k_dict.get("E0"))
        row = KineticsArrheniusBM(id=counts["k_arrbm"], kinetics_type=ktype, A_val=Av, A_unit=Au, n=nv, w0_val=w0v, w0_unit=w0u, E0_val=E0v, E0_unit=E0u, Tmin_val=Tminv, Tmin_unit=Tminu, Tmax_val=Tmaxv, Tmax_unit=Tmaxu, comment=k_dict.get("comment"))
        setattr(row, fk_col, fk_id); session.add(row); counts["k_arrbm"] += 1

    elif ktype == "Marcus":
        Av, Au = unpack_val_unit(k_dict.get("A"))
        beta_v, beta_u = unpack_val_unit(k_dict.get("beta"))
        wr_v, wr_u = unpack_val_unit(k_dict.get("wr"))
        wp_v, wp_u = unpack_val_unit(k_dict.get("wp"))
        lmbd_o_v, lmbd_o_u = unpack_val_unit(k_dict.get("lmbd_o"))
        row = KineticsMarcus(id=counts["k_marcus"], A_val=Av, A_unit=Au, n=to_float(k_dict.get("n")), beta_val=beta_v, beta_unit=beta_u, wr_val=wr_v, wr_unit=wr_u, wp_val=wp_v, wp_unit=wp_u, lmbd_o_val=lmbd_o_v, lmbd_o_unit=lmbd_o_u, comment=k_dict.get("comment"))
        setattr(row, fk_col, fk_id); session.add(row); session.flush()
        for i, val in enumerate(k_dict.get("lmbd_i_coefs", [])):
            session.add(KineticsMarcusCoefs(id=counts["k_marcus_c"], marcus_id=row.id, coef_index=i, coeff_value=to_float(val)))
            counts["k_marcus_c"] += 1
        counts["k_marcus"] += 1

    elif ktype == "Troe":
        hA, hAu, hn, hEa, hEau, _, _, Tminv, Tminu, Tmaxv, Tmaxu = ext(k_dict.get("arrheniusHigh", {}))
        lA, lAu, ln, lEa, lEau, _, _, _, _, _, _ = ext(k_dict.get("arrheniusLow", {}))
        T3v, T3u = unpack_val_unit(k_dict.get("T3")); T1v, T1u = unpack_val_unit(k_dict.get("T1")); T2v, T2u = unpack_val_unit(k_dict.get("T2"))
        row = KineticsTroe(id=counts["k_troe"], alpha=to_float(k_dict.get("alpha")), T3_val=T3v, T3_unit=T3u, T1_val=T1v, T1_unit=T1u, T2_val=T2v, T2_unit=T2u, high_A_val=hA, high_A_unit=hAu, high_n=hn, high_Ea_val=hEa, high_Ea_unit=hEau, low_A_val=lA, low_A_unit=lAu, low_n=ln, low_Ea_val=lEa, low_Ea_unit=lEau, Tmin_val=Tminv, Tmin_unit=Tminu, Tmax_val=Tmaxv, Tmax_unit=Tmaxu, comment=k_dict.get("comment"))
        setattr(row, fk_col, fk_id); session.add(row)
        for spec, val in k_dict.get("efficiencies", {}).items():
            eff_row = KineticsEfficiencies(id=counts["k_eff"], species_label=spec, efficiency=to_float(val)); setattr(eff_row, fk_col, fk_id); session.add(eff_row); counts["k_eff"] += 1
        counts["k_troe"] += 1

    elif ktype == "Lindemann":
        hA, hAu, hn, hEa, hEau, _, _, Tminv, Tminu, Tmaxv, Tmaxu = ext(k_dict.get("arrheniusHigh", {}))
        lA, lAu, ln, lEa, lEau, _, _, _, _, _, _ = ext(k_dict.get("arrheniusLow", {}))
        row = KineticsLindemann(id=counts["k_lind"], high_A_val=hA, high_A_unit=hAu, high_n=hn, high_Ea_val=hEa, high_Ea_unit=hEau, low_A_val=lA, low_A_unit=lAu, low_n=ln, low_Ea_val=lEa, low_Ea_unit=lEau, Tmin_val=Tminv, Tmin_unit=Tminu, Tmax_val=Tmaxv, Tmax_unit=Tmaxu, comment=k_dict.get("comment"))
        setattr(row, fk_col, fk_id); session.add(row)
        for spec, val in k_dict.get("efficiencies", {}).items():
            eff_row = KineticsEfficiencies(id=counts["k_eff"], species_label=spec, efficiency=to_float(val)); setattr(eff_row, fk_col, fk_id); session.add(eff_row); counts["k_eff"] += 1
        counts["k_lind"] += 1

    elif ktype == "ThirdBody":
        lA, lAu, ln, lEa, lEau, _, _, _, _, _, _ = ext(k_dict.get("arrheniusLow", {}))
        row = KineticsThirdBody(id=counts["k_3b"], low_A_val=lA, low_A_unit=lAu, low_n=ln, low_Ea_val=lEa, low_Ea_unit=lEau, comment=k_dict.get("comment"))
        setattr(row, fk_col, fk_id); session.add(row)
        for spec, val in k_dict.get("efficiencies", {}).items():
            eff_row = KineticsEfficiencies(id=counts["k_eff"], species_label=spec, efficiency=to_float(val)); setattr(eff_row, fk_col, fk_id); session.add(eff_row); counts["k_eff"] += 1
        counts["k_3b"] += 1

    elif ktype == "Chebyshev":
        Tminv, Tminu = unpack_val_unit(k_dict.get("Tmin")); Tmaxv, Tmaxu = unpack_val_unit(k_dict.get("Tmax"))
        Pminv, Pminu = unpack_val_unit(k_dict.get("Pmin")); Pmaxv, Pmaxu = unpack_val_unit(k_dict.get("Pmax"))
        row = KineticsChebyshev(id=counts["k_cheb"], Tmin_val=Tminv, Tmin_unit=Tminu, Tmax_val=Tmaxv, Tmax_unit=Tmaxu, Pmin_val=Pminv, Pmin_unit=Pminu, Pmax_val=Pmaxv, Pmax_unit=Pmaxu, degreeT=k_dict.get("degreeT"), degreeP=k_dict.get("degreeP"), comment=k_dict.get("comment"))
        setattr(row, fk_col, fk_id); session.add(row); session.flush()
        for r_i, c_row in enumerate(k_dict.get("coeffs", [])):
            for c_i, val in enumerate(c_row):
                session.add(KineticsChebyshevCoeffs(id=counts["k_cheb_c"], chebyshev_id=row.id, t_index=r_i, p_index=c_i, coeff_value=to_float(val)))
                counts["k_cheb_c"] += 1
        counts["k_cheb"] += 1

    elif ktype == "PDepArrhenius":
        Tminv, Tminu = unpack_val_unit(k_dict.get("Tmin")); Tmaxv, Tmaxu = unpack_val_unit(k_dict.get("Tmax"))
        row = KineticsPDepArrhenius(id=counts["k_pdep"], Tmin_val=Tminv, Tmin_unit=Tminu, Tmax_val=Tmaxv, Tmax_unit=Tmaxu, comment=k_dict.get("comment"))
        setattr(row, fk_col, fk_id); session.add(row); session.flush()
        pressures = k_dict.get("pressures", [None, None])
        p_list, pu = pressures[0], (pressures[1] if len(pressures)>1 else None)
        for pv, arr in zip(p_list or [], k_dict.get("arrhenius", [])):
            Av, Au, nv, Eav, Eau, _, _, _, _, _, _ = ext(arr)
            session.add(KineticsPDepArrheniusPressures(id=counts["k_pdep_p"], pdep_id=row.id, P_val=to_float(pv), P_unit=pu, A_val=Av, A_unit=Au, n=nv, Ea_val=Eav, Ea_unit=Eau))
            counts["k_pdep_p"] += 1
        counts["k_pdep"] += 1
        
    elif ktype == "KineticsModel":
        Tminv, Tminu = unpack_val_unit(k_dict.get("Tmin")); Tmaxv, Tmaxu = unpack_val_unit(k_dict.get("Tmax"))
        Pminv, Pminu = unpack_val_unit(k_dict.get("Pmin")); Pmaxv, Pmaxu = unpack_val_unit(k_dict.get("Pmax"))
        solute = k_dict.get("solute", {})
        if solute.get("type") == "SoluteTSDiffData":
            row = KineticsSoluteTSDiff(
                id=counts["k_solutets"],
                S_g=to_float(solute.get("S_g")), B_g=to_float(solute.get("B_g")), E_g=to_float(solute.get("E_g")), L_g=to_float(solute.get("L_g")), A_g=to_float(solute.get("A_g")), K_g=to_float(solute.get("K_g")),
                S_h=to_float(solute.get("S_h")), B_h=to_float(solute.get("B_h")), E_h=to_float(solute.get("E_h")), L_h=to_float(solute.get("L_h")), A_h=to_float(solute.get("A_h")), K_h=to_float(solute.get("K_h")),
                Tmin_val=Tminv, Tmin_unit=Tminu, Tmax_val=Tmaxv, Tmax_unit=Tmaxu, Pmin_val=Pminv, Pmin_unit=Pminu, Pmax_val=Pmaxv, Pmax_unit=Pmaxu,
                comment=k_dict.get("comment") or solute.get("comment")
            )
            setattr(row, fk_col, fk_id); session.add(row); counts["k_solutets"] += 1

def gen_db():
    engine = create_engine("sqlite:///kinetics.db", echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    SCHEMA_BASE.metadata.create_all(engine)

    counts = {"lib": 0, "lib_dict": 0, "lib_reac": 0, "lib_reac_spec": 0, "fam": 0, "fam_group": 0, "fam_forb": 0, "fam_tree": 0, 
              "fam_rule": 0, "fam_train_dict": 0, "fam_train_reac": 0, "fam_train_spec": 0,
              "k_arr": 0, "k_arrep": 0, "k_arrbm": 0, "k_marcus": 0, "k_marcus_c": 0,
              "k_troe": 0, "k_lind": 0, "k_3b": 0, "k_eff": 0,
              "k_cheb": 0, "k_cheb_c": 0, "k_pdep": 0, "k_pdep_p": 0, "k_solutets": 0}

    # Libraries
    if Path("yml/libraries").exists():
        for ldir in sorted(Path("yml/libraries").glob("*")):
            if not ldir.is_dir(): continue
            meta = {}
            if (ldir / "meta.yml").exists():
                with open(ldir / "meta.yml", "r") as f: meta = yaml.safe_load(f) or {}
            
            lib_id = counts["lib"]
            session.add(KineticsLibraries(id=lib_id, name=ldir.name, short_description=meta.get("short_description", ""), long_description=meta.get("long_description", "")))
            counts["lib"] += 1
            
            if (ldir / "dictionary.yml").exists():
                with open(ldir / "dictionary.yml", "r") as f:
                    for row in yaml.safe_load_all(f):
                        session.add(KineticsLibraryDictionary(id=counts["lib_dict"], library_id=lib_id, label=row["label"], adjacency_list=row["adjacency_list"]))
                        counts["lib_dict"] += 1

            if (ldir / "reactions.yml").exists():
                with open(ldir / "reactions.yml", "r") as f:
                    for row in yaml.safe_load_all(f):
                        r_id = counts["lib_reac"]
                        session.add(KineticsLibraryReactions(
                            id=r_id, library_id=lib_id, label=row["label"], degeneracy=row.get("degeneracy"), 
                            short_description=row.get("short_description", ""), long_description=row.get("long_description", ""), 
                            rank=row.get("rank"), allow_max_rate_violation=row.get("allow_max_rate_violation"), 
                            reversible=row.get("reversible"), elementary_high_p=row.get("elementary_high_p"), duplicate=row.get("duplicate")
                        ))
                        reactants, products = parse_reaction_label(row["label"])
                        for spec in reactants:
                            session.add(KineticsLibraryReactionSpecies(id=counts["lib_reac_spec"], library_reaction_id=r_id, species_label=spec, role='reactant')); counts["lib_reac_spec"] += 1
                        for spec in products:
                            session.add(KineticsLibraryReactionSpecies(id=counts["lib_reac_spec"], library_reaction_id=r_id, species_label=spec, role='product')); counts["lib_reac_spec"] += 1
                        
                        insert_kinetics(row.get("kinetics"), "library_reaction_id", r_id, session, counts)
                        counts["lib_reac"] += 1

    # Families
    label_to_id = {}
    if Path("yml/families").exists():
        for fdir in sorted(Path("yml/families").glob("*")):
            if not fdir.is_dir(): continue
            meta = {}
            if (fdir / "meta.yml").exists():
                with open(fdir / "meta.yml", "r") as f: meta = yaml.safe_load(f) or {}
                
            fam_id = counts["fam"]
            session.add(KineticsFamilies(
                id=fam_id, name=fdir.name, short_description=meta.get("short_description", ""), long_description=meta.get("long_description", ""),
                template=repr(meta.get("template")) if meta.get("template") else None, recipe=repr(meta.get("recipe")) if meta.get("recipe") else None,
                reversible=meta.get("reversible"), reverse_map=repr(meta.get("reverse_map")) if meta.get("reverse_map") else None,
                reactant_num=meta.get("reactant_num"), product_num=meta.get("product_num"), auto_generated=meta.get("auto_generated")
            ))
            counts["fam"] += 1
            
            if (fdir / "groups.yml").exists():
                with open(fdir / "groups.yml", "r") as f:
                    all_rows = list(yaml.safe_load_all(f))
                    for row in all_rows:
                        if row.get("forbidden"):
                            session.add(KineticsFamilyForbiddenGroups(id=counts["fam_forb"], family_id=fam_id, label=row["label"], group_adj_list=row["group"], short_description=row.get("short_description", ""), long_description=row.get("long_description", "")))
                            counts["fam_forb"] += 1
                        else:
                            label_to_id[row["label"]] = counts["fam_group"]
                            session.add(KineticsFamilyGroups(id=counts["fam_group"], family_id=fam_id, label=row["label"], group_adj_list=row["group"], short_description=row.get("short_description", ""), long_description=row.get("long_description", "")))
                            counts["fam_group"] += 1
                            
                    for row in all_rows:
                        if not row.get("forbidden"):
                            for child in row.get("children", []):
                                if child in label_to_id:
                                    session.add(KineticsFamilyGroupsTree(id=counts["fam_tree"], parent_id=label_to_id[row["label"]], child_id=label_to_id[child]))
                                    counts["fam_tree"] += 1

            if (fdir / "rules.yml").exists():
                with open(fdir / "rules.yml", "r") as f:
                    for row in yaml.safe_load_all(f):
                        r_id = counts["fam_rule"]
                        session.add(KineticsFamilyRules(
                            id=r_id, family_id=fam_id, label=row["label"], short_description=row.get("short_description", ""), 
                            long_description=row.get("long_description", ""), rank=row.get("rank"), allow_max_rate_violation=row.get("allow_max_rate_violation"), 
                            reversible=row.get("reversible"), elementary_high_p=row.get("elementary_high_p"), duplicate=row.get("duplicate")
                        ))
                        insert_kinetics(row.get("kinetics"), "family_rule_id", r_id, session, counts)
                        counts["fam_rule"] += 1

            if (fdir / "training/dictionary.yml").exists():
                with open(fdir / "training/dictionary.yml", "r") as f:
                    for row in yaml.safe_load_all(f):
                        session.add(KineticsFamilyTrainingDictionary(id=counts["fam_train_dict"], family_id=fam_id, label=row["label"], adjacency_list=row["adjacency_list"]))
                        counts["fam_train_dict"] += 1

            if (fdir / "training/reactions.yml").exists():
                with open(fdir / "training/reactions.yml", "r") as f:
                    for row in yaml.safe_load_all(f):
                        r_id = counts["fam_train_reac"]
                        session.add(KineticsFamilyTrainingReactions(
                            id=r_id, family_id=fam_id, label=row["label"], degeneracy=row.get("degeneracy"), short_description=row.get("short_description", ""), 
                            long_description=row.get("long_description", ""), rank=row.get("rank"), allow_max_rate_violation=row.get("allow_max_rate_violation"), 
                            reversible=row.get("reversible"), elementary_high_p=row.get("elementary_high_p"), duplicate=row.get("duplicate")
                        ))
                        reactants, products = parse_reaction_label(row["label"])
                        for spec in reactants:
                            session.add(KineticsFamilyTrainingReactionSpecies(id=counts["fam_train_spec"], training_reaction_id=r_id, species_label=spec, role='reactant')); counts["fam_train_spec"] += 1
                        for spec in products:
                            session.add(KineticsFamilyTrainingReactionSpecies(id=counts["fam_train_spec"], training_reaction_id=r_id, species_label=spec, role='product')); counts["fam_train_spec"] += 1
                        
                        insert_kinetics(row.get("kinetics"), "family_training_reaction_id", r_id, session, counts)
                        counts["fam_train_reac"] += 1

    try:
        session.commit()
        for view in [
            label_pairs_view_sql, kinetics_library_reaction_species_view_sql, kinetics_family_training_reaction_species_view_sql,
            all_library_kinetics_view_sql, all_family_rules_kinetics_view_sql, all_family_training_kinetics_view_sql, 
            kinetics_library_dictionary_view_sql, kinetics_family_groups_view_sql, kinetics_family_forbidden_groups_view_sql, 
            kinetics_family_training_dictionary_view_sql, kinetics_families_view_sql
        ]:
            session.execute(view)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error during gen_db commit: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    dump_db()
    Path("kinetics.db").rename("old.db")
    gen_db()
