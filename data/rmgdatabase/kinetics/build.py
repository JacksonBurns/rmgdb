


from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rmgdb.kinetics.schema import (
    KineticsLibraries, KineticsLibraryDictionary, KineticsLibraryReactions,
    KineticsFamilies, KineticsFamilyGroups, KineticsFamilyGroupsTree, KineticsFamilyRules,
    KineticsFamilyTrainingDictionary, KineticsFamilyTrainingReactions, KineticsData, SCHEMA_BASE
)
from rmgdb.kinetics.views import (
    label_pairs_view_sql, kinetics_library_reactions_view_sql, kinetics_family_rules_view_sql,
    kinetics_family_training_reactions_view_sql, kinetics_library_dictionary_view_sql,
    kinetics_family_groups_view_sql, kinetics_family_training_dictionary_view_sql, kinetics_families_view_sql
)
from rmgdatabase.common.tree_str_to_pairs import sketchy_conversion

engine = create_engine("sqlite:///kinetics.db", echo=False)
Session = sessionmaker(bind=engine)
SESSION = Session()
SCHEMA_BASE.metadata.create_all(engine)

COUNTS = {"lib": 0, "lib_dict": 0, "lib_reac": 0, "fam": 0, "fam_group": 0, "fam_tree": 0, "fam_rule": 0, "fam_train_dict": 0, "fam_train_reac": 0, "kdata": 0}
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
    "Troe", "ThirdBody", "SoluteData", "SurfaceArrhenius", "PDepArrhenius",
    "MultiArrhenius", "Article", "ArrheniusChargeTransfer", "SurfaceArrheniusBEP",
    "ArrheniusEP", "StickingCoefficient", "StickingCoefficientBEP", "Marcus",
    "ArrheniusChargeTransferBM", "Lindemann", "Wigner", "Eckart", "BimolecularRateConstant",
    "SurfaceChargeTransfer", "MultiPDepArrhenius", "SoluteTSDiffData"
]

def get_base_env():
    env = {name: make_spoofer(name) for name in SPOOF_CLASSES}
    env["forbidden"] = make_spoofer("forbidden")
    # env["ignore"] = "ignore"
    return env

def process_kinetics(kinetics, fk_col, fk_id):
    if not isinstance(kinetics, dict): return
    d = kinetics.get("data", {})
    
    A_v, A_u = parse_val_unit(d.get("A"))
    Ea_v, Ea_u = parse_val_unit(d.get("Ea"))
    T0_v, T0_u = parse_val_unit(d.get("T0"))
    w0_v, w0_u = parse_val_unit(d.get("w0"))
    E0_v, E0_u = parse_val_unit(d.get("E0"))
    Tmin_v, Tmin_u = parse_val_unit(d.get("Tmin"))
    Tmax_v, Tmax_u = parse_val_unit(d.get("Tmax"))
    
    # Safely extract n if it was wrapped in a tuple with uncertainties
    n_raw = d.get("n")
    n_v = n_raw[0] if isinstance(n_raw, (tuple, list)) and len(n_raw) > 0 else n_raw
    
    row = KineticsData(
        id=COUNTS["kdata"], type=kinetics.get("type"),
        A_val=to_float(A_v), A_unit=A_u, n=to_float(n_v),
        Ea_val=to_float(Ea_v), Ea_unit=Ea_u, 
        T0_val=to_float(T0_v), T0_unit=T0_u,
        w0_val=to_float(w0_v), w0_unit=w0_u, 
        E0_val=to_float(E0_v), E0_unit=E0_u,
        Tmin_val=to_float(Tmin_v), Tmin_unit=Tmin_u, 
        Tmax_val=to_float(Tmax_v), Tmax_unit=Tmax_u,
        comment=d.get("comment"),
        raw_data=repr(d) 
    )
    setattr(row, fk_col, fk_id)
    SESSION.add(row)
    COUNTS["kdata"] += 1

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
            id=r_id, library_id=lib_id, label=label, degeneracy=degeneracy, 
            short_description=shortDesc or "", long_description=longDesc or "", rank=rank,
            allow_max_rate_violation=allow_max_rate_violation, reversible=reversible, 
            elementary_high_p=elementary_high_p, duplicate=duplicate
        ))
        process_kinetics(kinetics, "library_reaction_id", r_id)
        COUNTS["lib_reac"] += 1

    env["entry"] = entry_spoof
    try: 
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
                id=COUNTS["fam_group"], family_id=fam_id, label=label, group_adj_list=group
            ))
            COUNTS["fam_group"] += 1
        
        def tree_spoof(tree_str):
            try:
                for p in sketchy_conversion(tree_str):
                    SESSION.add(KineticsFamilyGroupsTree(id=COUNTS["fam_tree"], parent_id=LABEL_TO_ID.get(p[0]), child_id=LABEL_TO_ID.get(p[1])))
                    COUNTS["fam_tree"] += 1
            except Exception: pass
                
        env["entry"] = grp_entry
        env["tree"] = tree_spoof
        
        try: 
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
                id=r_id, family_id=fam_id, label=label, 
                short_description=shortDesc or "", long_description=longDesc or "", rank=rank,
                allow_max_rate_violation=allow_max_rate_violation, reversible=reversible, 
                elementary_high_p=elementary_high_p, duplicate=duplicate
            ))
            process_kinetics(kinetics, "family_rule_id", r_id)
            COUNTS["fam_rule"] += 1
        env["entry"] = rule_entry
        try: exec(rule_file.read_text(), env)
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
                    id=r_id, family_id=fam_id, label=label, degeneracy=degeneracy, 
                    short_description=shortDesc or "", long_description=longDesc or "", rank=rank,
                    allow_max_rate_violation=allow_max_rate_violation, reversible=reversible, 
                    elementary_high_p=elementary_high_p, duplicate=duplicate
                ))
                process_kinetics(kinetics, "family_training_reaction_id", r_id)
                COUNTS["fam_train_reac"] += 1
            env["entry"] = tr_entry
            try: exec(tr_file.read_text(), env)
            except Exception as e: print(f"Error reading family training reactions for {name}: {e}")

if __name__ == "__main__":
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)  # many invalid escape sequence in RMG species' labels
        if Path("./original/libraries").exists():
            for p in Path("./original/libraries").glob("*"):
                if p.is_dir(): load_kinetics_library(p)
                
        if Path("./original/families").exists():
            for p in Path("./original/families").glob("*"):
                if p.is_dir(): load_kinetics_family(p)
            
        SESSION.commit()
        for view in [label_pairs_view_sql, kinetics_library_reactions_view_sql, kinetics_family_rules_view_sql, kinetics_family_training_reactions_view_sql, kinetics_library_dictionary_view_sql, kinetics_family_groups_view_sql, kinetics_family_training_dictionary_view_sql, kinetics_families_view_sql]:
            SESSION.execute(view)
        SESSION.commit()
        SESSION.close()
