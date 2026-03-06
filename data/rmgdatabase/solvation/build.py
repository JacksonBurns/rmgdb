from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rmgdb.solvation.schema import (
    Groups, GroupsTree, SoluteLibraries, SolventLibraries, 
    SoluteData, SolventData, DataCountGAV, DataCountSolvent, SCHEMA_BASE
)
from rmgdb.solvation.views import (
    label_pairs_view_sql, solute_libraries_view_sql, 
    solvent_libraries_view_sql, solute_groups_view_sql
)
from rmgdatabase.common.tree_str_to_pairs import sketchy_conversion

engine = create_engine("sqlite:///solvation.db", echo=False)
Session = sessionmaker(bind=engine)
SESSION = Session()
SCHEMA_BASE.metadata.create_all(engine)

def SoluteDataSpoof(**kwargs): return {"type": "SoluteData", "data": kwargs}
def SolventDataSpoof(**kwargs): return {"type": "SolventData", "data": kwargs}
def DataCountGAVSpoof(**kwargs): return {"type": "DataCountGAV", "data": kwargs}
def DataCountSolventSpoof(**kwargs): return {"type": "DataCountSolvent", "data": kwargs}

COUNTS = {"group": 0, "solute_lib": 0, "solvent_lib": 0, "solute_data": 0, "solvent_data": 0, "count_gav": 0, "count_solvent": 0, "tree": 0}
LABEL_TO_ID = {None: None}
CURRENT_NAME = ""

def safe_tup(val):
    if isinstance(val, tuple): return val[0], (val[1] if len(val)>1 else None)
    return val, None

def entry_spoof(target, col, counter_key):
    def wrapper(*, index, label, molecule=None, group=None, solute=None, solvent=None, dataCount=None, shortDesc="", longDesc=""):
        kwargs = dict(id=COUNTS[counter_key], name=CURRENT_NAME, short_description=shortDesc, long_description=longDesc, label=label)
        
        if target == Groups:
            kwargs["group"] = group
            LABEL_TO_ID[label] = COUNTS[counter_key]
            if isinstance(solute, str): kwargs["solute_pointer"] = solute
        else:
            kwargs["molecule"] = repr(molecule) if isinstance(molecule, list) else molecule
            
        SESSION.add(target(**kwargs))
        
        if solute and isinstance(solute, dict) and solute["type"] == "SoluteData":
            d = solute["data"]
            row = SoluteData(id=COUNTS["solute_data"], S=d.get("S"), B=d.get("B"), E=d.get("E"), L=d.get("L"), A=d.get("A"), V=d.get("V"))
            setattr(row, col, COUNTS[counter_key])
            SESSION.add(row)
            COUNTS["solute_data"] += 1
            
        if solvent and isinstance(solvent, dict) and solvent["type"] == "SolventData":
            d = solvent["data"]
            row = SolventData(
                id=COUNTS["solvent_data"], 
                s_g=d.get("s_g"), b_g=d.get("b_g"), e_g=d.get("e_g"), l_g=d.get("l_g"), a_g=d.get("a_g"), c_g=d.get("c_g"),
                s_h=d.get("s_h"), b_h=d.get("b_h"), e_h=d.get("e_h"), l_h=d.get("l_h"), a_h=d.get("a_h"), c_h=d.get("c_h"),
                A=d.get("A"), B=d.get("B"), C=d.get("C"), D=d.get("D"), E=d.get("E"),
                alpha=d.get("alpha"), beta=d.get("beta"), eps=d.get("eps"), n=d.get("n"), name_in_coolprop=d.get("name_in_coolprop")
            )
            setattr(row, col, COUNTS[counter_key])
            SESSION.add(row)
            COUNTS["solvent_data"] += 1
            
        if dataCount and isinstance(dataCount, dict):
            if dataCount["type"] == "DataCountGAV":
                d = dataCount["data"]
                row = DataCountGAV(id=COUNTS["count_gav"], group_parent_id=COUNTS[counter_key], S=d.get("S"), B=d.get("B"), E=d.get("E"), L=d.get("L"), A=d.get("A"))
                SESSION.add(row)
                COUNTS["count_gav"] += 1
            elif dataCount["type"] == "DataCountSolvent":
                d = dataCount["data"]
                g_val, g_unit = safe_tup(d.get("dGsolvMAE"))
                h_val, h_unit = safe_tup(d.get("dHsolvMAE"))
                row = DataCountSolvent(
                    id=COUNTS["count_solvent"], solvent_library_parent_id=COUNTS[counter_key],
                    dGsolvCount=d.get("dGsolvCount"), dGsolvMAE_val=g_val, dGsolvMAE_unit=g_unit,
                    dHsolvCount=d.get("dHsolvCount"), dHsolvMAE_val=h_val, dHsolvMAE_unit=h_unit
                )
                SESSION.add(row)
                COUNTS["count_solvent"] += 1
        COUNTS[counter_key] += 1
    return wrapper

def tree_spoof(tree_str):
    for p in sketchy_conversion(tree_str):
        SESSION.add(GroupsTree(id=COUNTS["tree"], parent_id=LABEL_TO_ID.get(p[0]), child_id=LABEL_TO_ID.get(p[1])))
        COUNTS["tree"] += 1

def load_files(folder, target, col, counter_key, do_tree=False):
    global CURRENT_NAME
    tdir = Path(f"./original/{folder}")
    if not tdir.exists(): return
    for f in tdir.glob("*.py"):
        CURRENT_NAME = f.stem
        env = {
            "entry": entry_spoof(target, col, counter_key), 
            "SoluteData": SoluteDataSpoof, 
            "SolventData": SolventDataSpoof,
            "DataCountGAV": DataCountGAVSpoof,
            "DataCountSolvent": DataCountSolventSpoof
        }
        if do_tree: env["tree"] = tree_spoof
        try: exec(f.read_text(), env)
        except Exception: pass


load_files("groups", Groups, "group_parent_id", "group", do_tree=True)

tdir = Path("./original/libraries")
if tdir.exists():
    for f in tdir.glob("*.py"):
        CURRENT_NAME = f.stem
        env = {
            "SoluteData": SoluteDataSpoof, 
            "SolventData": SolventDataSpoof,
            "DataCountGAV": DataCountGAVSpoof,
            "DataCountSolvent": DataCountSolventSpoof
        }
        if f.stem == "solvent":
            env["entry"] = entry_spoof(SolventLibraries, "solvent_library_parent_id", "solvent_lib")
        else:
            env["entry"] = entry_spoof(SoluteLibraries, "solute_library_parent_id", "solute_lib")
        try: exec(f.read_text(), env)
        except Exception: pass

SESSION.commit()
for view in [solute_groups_view_sql, solute_libraries_view_sql, solvent_libraries_view_sql, label_pairs_view_sql]:
    SESSION.execute(view)
SESSION.commit()
SESSION.close()
