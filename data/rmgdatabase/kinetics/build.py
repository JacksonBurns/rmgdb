import warnings
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rmgdb.kinetics.schema import (
    KineticsLibraries, KineticsLibraryDictionary, KineticsLibraryReactions, KineticsLibraryReactionSpecies,
    KineticsFamilies, KineticsFamilyGroups, KineticsFamilyForbiddenGroups, KineticsFamilyGroupsTree, KineticsFamilyRules,
    KineticsFamilyTrainingDictionary, KineticsFamilyTrainingReactions, KineticsFamilyTrainingReactionSpecies,
    KineticsArrhenius, KineticsArrheniusEP, KineticsArrheniusBM, KineticsMarcus, KineticsMarcusCoefs, 
    KineticsTroe, KineticsLindemann, KineticsThirdBody, KineticsEfficiencies, KineticsChebyshev, KineticsChebyshevCoeffs,
    KineticsPDepArrhenius, KineticsPDepArrheniusPressures, KineticsSoluteTSDiff, SCHEMA_BASE
)
from rmgdb.kinetics.views import (
    label_pairs_view_sql, kinetics_library_reaction_species_view_sql, kinetics_family_training_reaction_species_view_sql,
    all_library_kinetics_view_sql, all_family_rules_kinetics_view_sql, all_family_training_kinetics_view_sql, 
    kinetics_library_dictionary_view_sql, kinetics_family_groups_view_sql, kinetics_family_forbidden_groups_view_sql, 
    kinetics_family_training_dictionary_view_sql, kinetics_families_view_sql
)
from rmgdatabase.common.tree_str_to_pairs import sketchy_conversion

engine = create_engine("sqlite:///kinetics.db", echo=False)
Session = sessionmaker(bind=engine)
SESSION = Session()
SCHEMA_BASE.metadata.create_all(engine)

COUNTS = {"lib": 0, "lib_dict": 0, "lib_reac": 0, "lib_reac_spec": 0, "fam": 0, "fam_group": 0, "fam_forb": 0, "fam_tree": 0, 
          "fam_rule": 0, "fam_train_dict": 0, "fam_train_reac": 0, "fam_train_spec": 0,
          "k_arr": 0, "k_arrep": 0, "k_arrbm": 0, "k_marcus": 0, "k_marcus_c": 0,
          "k_troe": 0, "k_lind": 0, "k_3b": 0, "k_eff": 0,
          "k_cheb": 0, "k_cheb_c": 0, "k_pdep": 0, "k_pdep_p": 0, "k_solutets": 0}
LABEL_TO_ID = {None: None}

def parse_val_unit(tup):
    if isinstance(tup, (tuple, list)) and len(tup) > 0:
        v = tup[0]
        u = tup[1] if len(tup) > 1 and isinstance(tup[1], str) and tup[1] not in ['+|-', '*|/'] else None
        return v, u
    return tup, None

def to_float(val):
    if val is None: return None
    try: return float(val)
    except (TypeError, ValueError): return None

def make_spoofer(name):
    def spoof(*args, **kwargs): return {"type": name, "data": kwargs}
    return spoof

SPOOF_CLASSES = [
    "Arrhenius", "ArrheniusBM", "RateUncertainty", "Chebyshev", "KineticsModel",
    "Troe", "ThirdBody", "SoluteData", "SoluteTSDiffData", "SurfaceArrhenius", "PDepArrhenius",
    "MultiArrhenius", "MultiPDepArrhenius", "Article", "ArrheniusChargeTransfer", "SurfaceArrheniusBEP",
    "ArrheniusEP", "StickingCoefficient", "StickingCoefficientBEP", "Marcus",
    "ArrheniusChargeTransferBM", "Lindemann", "Wigner", "Eckart", "BimolecularRateConstant",
    "SurfaceChargeTransfer"
]

def get_base_env():
    env = {name: make_spoofer(name) for name in SPOOF_CLASSES}
    env["ignore"] = "ignore"
    return env

def extract_base_arr(d):
    Av, Au = parse_val_unit(d.get("A"))
    Eav, Eau = parse_val_unit(d.get("Ea"))
    T0v, T0u = parse_val_unit(d.get("T0"))
    Tminv, Tminu = parse_val_unit(d.get("Tmin"))
    Tmaxv, Tmaxu = parse_val_unit(d.get("Tmax"))
    nv_raw = d.get("n")
    nv = nv_raw[0] if isinstance(nv_raw, (tuple, list)) and len(nv_raw)>0 else nv_raw
    return to_float(Av), Au, to_float(nv), to_float(Eav), Eau, to_float(T0v), T0u, to_float(Tminv), Tminu, to_float(Tmaxv), Tmaxu

def save_efficiencies(eff_dict, fk_col, fk_id):
    if not eff_dict: return
    for spec, val in eff_dict.items():
        row = KineticsEfficiencies(id=COUNTS["k_eff"], species_label=spec, efficiency=to_float(val))
        setattr(row, fk_col, fk_id)
        SESSION.add(row)
        COUNTS["k_eff"] += 1

def process_kinetics(kinetics, fk_col, fk_id):
    if not isinstance(kinetics, dict): return
    ktype = kinetics.get("type")
    d = kinetics.get("data", {})
    
    if ktype in ["Arrhenius", "SurfaceArrhenius", "StickingCoefficient", "ArrheniusChargeTransfer", "SurfaceChargeTransfer"]:
        Av, Au, nv, Eav, Eau, T0v, T0u, Tminv, Tminu, Tmaxv, Tmaxu = extract_base_arr(d)
        row = KineticsArrhenius(id=COUNTS["k_arr"], kinetics_type=ktype, A_val=Av, A_unit=Au, n=nv, Ea_val=Eav, Ea_unit=Eau, T0_val=T0v, T0_unit=T0u, Tmin_val=Tminv, Tmin_unit=Tminu, Tmax_val=Tmaxv, Tmax_unit=Tmaxu, comment=d.get("comment"))
        setattr(row, fk_col, fk_id); SESSION.add(row); COUNTS["k_arr"] += 1
        
    elif ktype == "MultiArrhenius":
        for arr in d.get("arrhenius", []):
            if isinstance(arr, dict): process_kinetics(arr, fk_col, fk_id)

    elif ktype == "MultiPDepArrhenius":
        for arr in d.get("arrhenius", []):
            if isinstance(arr, dict): process_kinetics(arr, fk_col, fk_id)

    elif ktype in ["ArrheniusEP", "SurfaceArrheniusBEP", "StickingCoefficientBEP"]:
        Av, Au, nv, _, _, _, _, Tminv, Tminu, Tmaxv, Tmaxu = extract_base_arr(d)
        E0v, E0u = parse_val_unit(d.get("E0"))
        row = KineticsArrheniusEP(id=COUNTS["k_arrep"], kinetics_type=ktype, A_val=Av, A_unit=Au, n=nv, alpha=to_float(d.get("alpha")), E0_val=to_float(E0v), E0_unit=E0u, Tmin_val=Tminv, Tmin_unit=Tminu, Tmax_val=Tmaxv, Tmax_unit=Tmaxu, comment=d.get("comment"))
        setattr(row, fk_col, fk_id); SESSION.add(row); COUNTS["k_arrep"] += 1

    elif ktype in ["ArrheniusBM", "ArrheniusChargeTransferBM"]:
        Av, Au, nv, _, _, _, _, Tminv, Tminu, Tmaxv, Tmaxu = extract_base_arr(d)
        w0v, w0u = parse_val_unit(d.get("w0")); E0v, E0u = parse_val_unit(d.get("E0"))
        row = KineticsArrheniusBM(id=COUNTS["k_arrbm"], kinetics_type=ktype, A_val=Av, A_unit=Au, n=nv, w0_val=to_float(w0v), w0_unit=w0u, E0_val=to_float(E0v), E0_unit=E0u, Tmin_val=Tminv, Tmin_unit=Tminu, Tmax_val=Tmaxv, Tmax_unit=Tmaxu, comment=d.get("comment"))
        setattr(row, fk_col, fk_id); SESSION.add(row); COUNTS["k_arrbm"] += 1

    elif ktype == "Marcus":
        Av, Au = parse_val_unit(d.get("A"))
        nv_raw = d.get("n")
        nv = nv_raw[0] if isinstance(nv_raw, (tuple, list)) and len(nv_raw)>0 else nv_raw
        beta_v, beta_u = parse_val_unit(d.get("beta"))
        wr_v, wr_u = parse_val_unit(d.get("wr"))
        wp_v, wp_u = parse_val_unit(d.get("wp"))
        lmbd_o_v, lmbd_o_u = parse_val_unit(d.get("lmbd_o"))

        row = KineticsMarcus(
            id=COUNTS["k_marcus"], A_val=to_float(Av), A_unit=Au, n=to_float(nv),
            beta_val=to_float(beta_v), beta_unit=beta_u, wr_val=to_float(wr_v), wr_unit=wr_u,
            wp_val=to_float(wp_v), wp_unit=wp_u, lmbd_o_val=to_float(lmbd_o_v), lmbd_o_unit=lmbd_o_u,
            comment=d.get("comment")
        )
        setattr(row, fk_col, fk_id); SESSION.add(row); SESSION.flush()
        
        coefs = d.get("lmbd_i_coefs", [])
        if coefs:
            for i, val in enumerate(coefs):
                SESSION.add(KineticsMarcusCoefs(id=COUNTS["k_marcus_c"], marcus_id=row.id, coef_index=i, coeff_value=to_float(val)))
                COUNTS["k_marcus_c"] += 1
        COUNTS["k_marcus"] += 1

    elif ktype == "Troe":
        hA, hAu, hn, hEa, hEau, _, _, Tminv, Tminu, Tmaxv, Tmaxu = extract_base_arr(d.get("arrheniusHigh", {}).get("data", {}))
        lA, lAu, ln, lEa, lEau, _, _, _, _, _, _ = extract_base_arr(d.get("arrheniusLow", {}).get("data", {}))
        T3v, T3u = parse_val_unit(d.get("T3")); T1v, T1u = parse_val_unit(d.get("T1")); T2v, T2u = parse_val_unit(d.get("T2"))
        row = KineticsTroe(id=COUNTS["k_troe"], alpha=to_float(d.get("alpha")), T3_val=to_float(T3v), T3_unit=T3u, T1_val=to_float(T1v), T1_unit=T1u, T2_val=to_float(T2v), T2_unit=T2u, high_A_val=hA, high_A_unit=hAu, high_n=hn, high_Ea_val=hEa, high_Ea_unit=hEau, low_A_val=lA, low_A_unit=lAu, low_n=ln, low_Ea_val=lEa, low_Ea_unit=lEau, Tmin_val=Tminv, Tmin_unit=Tminu, Tmax_val=Tmaxv, Tmax_unit=Tmaxu, comment=d.get("comment"))
        setattr(row, fk_col, fk_id); SESSION.add(row); save_efficiencies(d.get("efficiencies"), fk_col, fk_id); COUNTS["k_troe"] += 1

    elif ktype == "Lindemann":
        hA, hAu, hn, hEa, hEau, _, _, Tminv, Tminu, Tmaxv, Tmaxu = extract_base_arr(d.get("arrheniusHigh", {}).get("data", {}))
        lA, lAu, ln, lEa, lEau, _, _, _, _, _, _ = extract_base_arr(d.get("arrheniusLow", {}).get("data", {}))
        row = KineticsLindemann(id=COUNTS["k_lind"], high_A_val=hA, high_A_unit=hAu, high_n=hn, high_Ea_val=hEa, high_Ea_unit=hEau, low_A_val=lA, low_A_unit=lAu, low_n=ln, low_Ea_val=lEa, low_Ea_unit=lEau, Tmin_val=Tminv, Tmin_unit=Tminu, Tmax_val=Tmaxv, Tmax_unit=Tmaxu, comment=d.get("comment"))
        setattr(row, fk_col, fk_id); SESSION.add(row); save_efficiencies(d.get("efficiencies"), fk_col, fk_id); COUNTS["k_lind"] += 1

    elif ktype == "ThirdBody":
        lA, lAu, ln, lEa, lEau, _, _, _, _, _, _ = extract_base_arr(d.get("arrheniusLow", {}).get("data", {}))
        row = KineticsThirdBody(id=COUNTS["k_3b"], low_A_val=lA, low_A_unit=lAu, low_n=ln, low_Ea_val=lEa, low_Ea_unit=lEau, comment=d.get("comment"))
        setattr(row, fk_col, fk_id); SESSION.add(row); save_efficiencies(d.get("efficiencies"), fk_col, fk_id); COUNTS["k_3b"] += 1

    elif ktype == "Chebyshev":
        Tminv, Tminu = parse_val_unit(d.get("Tmin")); Tmaxv, Tmaxu = parse_val_unit(d.get("Tmax"))
        Pminv, Pminu = parse_val_unit(d.get("Pmin")); Pmaxv, Pmaxu = parse_val_unit(d.get("Pmax"))
        row = KineticsChebyshev(id=COUNTS["k_cheb"], Tmin_val=to_float(Tminv), Tmin_unit=Tminu, Tmax_val=to_float(Tmaxv), Tmax_unit=Tmaxu, Pmin_val=to_float(Pminv), Pmin_unit=Pminu, Pmax_val=to_float(Pmaxv), Pmax_unit=Pmaxu, degreeT=d.get("degreeT"), degreeP=d.get("degreeP"), comment=d.get("comment"))
        setattr(row, fk_col, fk_id); SESSION.add(row); SESSION.flush()
        for r_i, c_row in enumerate(d.get("coeffs", [])):
            for c_i, val in enumerate(c_row):
                SESSION.add(KineticsChebyshevCoeffs(id=COUNTS["k_cheb_c"], chebyshev_id=row.id, t_index=r_i, p_index=c_i, coeff_value=to_float(val)))
                COUNTS["k_cheb_c"] += 1
        COUNTS["k_cheb"] += 1

    elif ktype == "PDepArrhenius":
        Tminv, Tminu = parse_val_unit(d.get("Tmin")); Tmaxv, Tmaxu = parse_val_unit(d.get("Tmax"))
        row = KineticsPDepArrhenius(id=COUNTS["k_pdep"], Tmin_val=to_float(Tminv), Tmin_unit=Tminu, Tmax_val=to_float(Tmaxv), Tmax_unit=Tmaxu, comment=d.get("comment"))
        setattr(row, fk_col, fk_id); SESSION.add(row); SESSION.flush()
        pressures, pu = parse_val_unit(d.get("pressures"))
        arrs = d.get("arrhenius", [])
        if pressures and arrs and len(pressures) == len(arrs):
            for pv, arr in zip(pressures, arrs):
                Av, Au, nv, Eav, Eau, _, _, _, _, _, _ = extract_base_arr(arr.get("data", {}))
                SESSION.add(KineticsPDepArrheniusPressures(id=COUNTS["k_pdep_p"], pdep_id=row.id, P_val=to_float(pv), P_unit=pu, A_val=Av, A_unit=Au, n=nv, Ea_val=Eav, Ea_unit=Eau))
                COUNTS["k_pdep_p"] += 1
        COUNTS["k_pdep"] += 1
        
    elif ktype == "KineticsModel":
        Tminv, Tminu = parse_val_unit(d.get("Tmin"))
        Tmaxv, Tmaxu = parse_val_unit(d.get("Tmax"))
        Pminv, Pminu = parse_val_unit(d.get("Pmin"))
        Pmaxv, Pmaxu = parse_val_unit(d.get("Pmax"))
        solute = d.get("solute", {})
        if isinstance(solute, dict) and solute.get("type") == "SoluteTSDiffData":
            sd = solute.get("data", {})
            row = KineticsSoluteTSDiff(
                id=COUNTS["k_solutets"],
                S_g=to_float(sd.get("S_g")), B_g=to_float(sd.get("B_g")), E_g=to_float(sd.get("E_g")), L_g=to_float(sd.get("L_g")), A_g=to_float(sd.get("A_g")), K_g=to_float(sd.get("K_g")),
                S_h=to_float(sd.get("S_h")), B_h=to_float(sd.get("B_h")), E_h=to_float(sd.get("E_h")), L_h=to_float(sd.get("L_h")), A_h=to_float(sd.get("A_h")), K_h=to_float(sd.get("K_h")),
                Tmin_val=to_float(Tminv), Tmin_unit=Tminu, Tmax_val=to_float(Tmaxv), Tmax_unit=Tmaxu,
                Pmin_val=to_float(Pminv), Pmin_unit=Pminu, Pmax_val=to_float(Pmaxv), Pmax_unit=Pmaxu,
                comment=d.get("comment") or sd.get("comment")
            )
            setattr(row, fk_col, fk_id)
            SESSION.add(row)
            COUNTS["k_solutets"] += 1

def parse_reaction_label(label):
    if '<=>' in label: r, p = label.split('<=>')
    elif '=>' in label: r, p = label.split('=>')
    elif '=' in label: r, p = label.split('=')
    else: return [], []
    return [x.strip() for x in r.split('+') if x.strip()], [x.strip() for x in p.split('+') if x.strip()]

def parse_dict(filepath):
    entries, current_adj = [], []
    current_label = None
    with open(filepath, 'r') as f:
        for line in f:
            if not line.strip():
                if current_label:
                    entries.append((current_label, "".join(current_adj).strip()))
                    current_label, current_adj = None, []
                continue
            parts = line.split()
            if line.startswith(" ") or line.startswith("\t") or parts[0].isdigit() or parts[0] in ["multiplicity", "elec"]:
                current_adj.append(line)
            else:
                if current_label: entries.append((current_label, "".join(current_adj).strip()))
                current_label, current_adj = line.strip(), []
        if current_label: entries.append((current_label, "".join(current_adj).strip()))
    return entries

def load_kinetics_library(folder):
    name = folder.stem
    env = get_base_env()
    env.update({"name": "", "shortDesc": "", "longDesc": ""})
    
    reac_file = folder / "reactions.py"
    if not reac_file.exists(): return
    
    lib_id = COUNTS["lib"]
    lib_obj = KineticsLibraries(id=lib_id, name=name, short_description="", long_description="")
    SESSION.add(lib_obj)
    COUNTS["lib"] += 1

    dict_file = folder / "dictionary.txt"
    if dict_file.exists():
        for label, adj in parse_dict(dict_file):
            SESSION.add(KineticsLibraryDictionary(id=COUNTS["lib_dict"], library_id=lib_id, label=label, adjacency_list=adj))
            COUNTS["lib_dict"] += 1
            
    def entry_spoof(*, index=None, label="", degeneracy=None, kinetics=None, shortDesc="", longDesc="", rank=None, 
                    allow_max_rate_violation=None, reversible=None, elementary_high_p=None, duplicate=None, **kwargs):
        r_id = COUNTS["lib_reac"]
        SESSION.add(KineticsLibraryReactions(
            id=r_id, library_id=lib_id, label=label, degeneracy=degeneracy, short_description=shortDesc or "", 
            long_description=longDesc or "", rank=rank, allow_max_rate_violation=allow_max_rate_violation, 
            reversible=reversible, elementary_high_p=elementary_high_p, duplicate=duplicate
        ))
        
        reactants, products = parse_reaction_label(label)
        for spec in reactants:
            SESSION.add(KineticsLibraryReactionSpecies(id=COUNTS["lib_reac_spec"], library_reaction_id=r_id, species_label=spec, role='reactant'))
            COUNTS["lib_reac_spec"] += 1
        for spec in products:
            SESSION.add(KineticsLibraryReactionSpecies(id=COUNTS["lib_reac_spec"], library_reaction_id=r_id, species_label=spec, role='product'))
            COUNTS["lib_reac_spec"] += 1

        process_kinetics(kinetics, "library_reaction_id", r_id)
        COUNTS["lib_reac"] += 1

    env["entry"] = entry_spoof
    try: 
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            exec(reac_file.read_text(), env)
        lib_obj.short_description = env.get("shortDesc", "") or ""
        lib_obj.long_description = env.get("longDesc", "") or ""
    except Exception as e: print(f"Error reading library {name}: {e}")

def load_kinetics_family(folder):
    name = folder.stem
    fam_id = COUNTS["fam"]
    
    fam_obj = KineticsFamilies(id=fam_id, name=name, short_description="", long_description="")
    SESSION.add(fam_obj)
    COUNTS["fam"] += 1
    
    header_data = {}
    def template_spoof(**kwargs): header_data["template"] = kwargs
    def recipe_spoof(**kwargs): header_data["recipe"] = kwargs
    
    env = get_base_env()
    env.update({
        "name": "", "shortDesc": "", "longDesc": "", "reversible": True, "reverseMap": {}, "autoGenerated": False,
        "reactantNum": None, "productNum": None, "template": template_spoof, "recipe": recipe_spoof,
    })
    
    grp_file = folder / "groups.py"
    if grp_file.exists():
        def grp_entry(*, index=None, label="", group="", shortDesc="", longDesc="", kinetics=None, **kwargs):
            LABEL_TO_ID[label] = COUNTS["fam_group"]
            SESSION.add(KineticsFamilyGroups(
                id=COUNTS["fam_group"], family_id=fam_id, label=label, group_adj_list=group,
                short_description=shortDesc or "", long_description=longDesc or ""
            ))
            COUNTS["fam_group"] += 1
            
        def forbidden_spoof(*, label="", group="", shortDesc="", longDesc="", **kwargs):
            SESSION.add(KineticsFamilyForbiddenGroups(
                id=COUNTS["fam_forb"], family_id=fam_id, label=label, group_adj_list=group,
                short_description=shortDesc or "", long_description=longDesc or ""
            ))
            COUNTS["fam_forb"] += 1
        
        def tree_spoof(tree_str):
            try:
                for p in sketchy_conversion(tree_str):
                    SESSION.add(KineticsFamilyGroupsTree(id=COUNTS["fam_tree"], parent_id=LABEL_TO_ID.get(p[0]), child_id=LABEL_TO_ID.get(p[1])))
                    COUNTS["fam_tree"] += 1
            except Exception: pass
                
        env["entry"] = grp_entry
        env["forbidden"] = forbidden_spoof
        env["tree"] = tree_spoof
        
        try: 
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                exec(grp_file.read_text(), env)
            fam_obj.short_description = env.get("shortDesc", "") or ""
            fam_obj.long_description = env.get("longDesc", "") or ""
            fam_obj.template = repr(header_data.get("template", {}))
            fam_obj.recipe = repr(header_data.get("recipe", {}))
            fam_obj.reversible = env.get("reversible", True)
            fam_obj.reverse_map = repr(env.get("reverseMap", {}))
            fam_obj.reactant_num = env.get("reactantNum")
            fam_obj.product_num = env.get("productNum")
            fam_obj.auto_generated = env.get("autoGenerated", False)
        except Exception as e: print(f"Error reading family groups for {name}: {e}")
        
    rule_file = folder / "rules.py"
    if rule_file.exists():
        def rule_entry(*, index=None, label="", kinetics=None, shortDesc="", longDesc="", rank=None, 
                       allow_max_rate_violation=None, reversible=None, elementary_high_p=None, duplicate=None, **kwargs):
            r_id = COUNTS["fam_rule"]
            SESSION.add(KineticsFamilyRules(
                id=r_id, family_id=fam_id, label=label, short_description=shortDesc or "", long_description=longDesc or "", 
                rank=rank, allow_max_rate_violation=allow_max_rate_violation, reversible=reversible, 
                elementary_high_p=elementary_high_p, duplicate=duplicate
            ))
            process_kinetics(kinetics, "family_rule_id", r_id)
            COUNTS["fam_rule"] += 1
        env["entry"] = rule_entry
        try: 
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                exec(rule_file.read_text(), env)
        except Exception as e: print(f"Error reading family rules for {name}: {e}")
        
    train_dir = folder / "training"
    if train_dir.exists():
        td_file = train_dir / "dictionary.txt"
        if td_file.exists():
            for label, adj in parse_dict(td_file):
                SESSION.add(KineticsFamilyTrainingDictionary(id=COUNTS["fam_train_dict"], family_id=fam_id, label=label, adjacency_list=adj))
                COUNTS["fam_train_dict"] += 1
                
        tr_file = train_dir / "reactions.py"
        if tr_file.exists():
            def tr_entry(*, index=None, label="", degeneracy=None, kinetics=None, shortDesc="", longDesc="", rank=None, 
                         allow_max_rate_violation=None, reversible=None, elementary_high_p=None, duplicate=None, **kwargs):
                r_id = COUNTS["fam_train_reac"]
                SESSION.add(KineticsFamilyTrainingReactions(
                    id=r_id, family_id=fam_id, label=label, degeneracy=degeneracy, short_description=shortDesc or "", 
                    long_description=longDesc or "", rank=rank, allow_max_rate_violation=allow_max_rate_violation, 
                    reversible=reversible, elementary_high_p=elementary_high_p, duplicate=duplicate
                ))
                
                reactants, products = parse_reaction_label(label)
                for spec in reactants:
                    SESSION.add(KineticsFamilyTrainingReactionSpecies(id=COUNTS["fam_train_spec"], training_reaction_id=r_id, species_label=spec, role='reactant'))
                    COUNTS["fam_train_spec"] += 1
                for spec in products:
                    SESSION.add(KineticsFamilyTrainingReactionSpecies(id=COUNTS["fam_train_spec"], training_reaction_id=r_id, species_label=spec, role='product'))
                    COUNTS["fam_train_spec"] += 1

                process_kinetics(kinetics, "family_training_reaction_id", r_id)
                COUNTS["fam_train_reac"] += 1
            env["entry"] = tr_entry
            try: 
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    exec(tr_file.read_text(), env)
            except Exception as e: print(f"Error reading family training reactions for {name}: {e}")

if __name__ == "__main__":
    if Path("./original/libraries").exists():
        for p in Path("./original/libraries").glob("*"):
            if p.is_dir(): load_kinetics_library(p)
            
    if Path("./original/families").exists():
        for p in Path("./original/families").glob("*"):
            if p.is_dir(): load_kinetics_family(p)
        
    SESSION.commit()
    for view in [
        label_pairs_view_sql, kinetics_library_reaction_species_view_sql, kinetics_family_training_reaction_species_view_sql,
        all_library_kinetics_view_sql, all_family_rules_kinetics_view_sql, all_family_training_kinetics_view_sql, 
        kinetics_library_dictionary_view_sql, kinetics_family_groups_view_sql, kinetics_family_forbidden_groups_view_sql, 
        kinetics_family_training_dictionary_view_sql, kinetics_families_view_sql
    ]:
        SESSION.execute(view)
    SESSION.commit()
    SESSION.close()
