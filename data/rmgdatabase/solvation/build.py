import warnings
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

def safe_tup(val):
    if isinstance(val, tuple): return val[0], (val[1] if len(val)>1 else None)
    return val, None

if __name__ == "__main__":
    # GROUPS
    tdir = Path("./original/groups")
    if tdir.exists():
        for f in sorted(tdir.glob("*.py")):
            label_to_id = {}
            name = f.stem
            
            def grp_entry(*, index=None, label="", group=None, solute=None, shortDesc="", longDesc="", dataCount=None, **kwargs):
                label_to_id[label] = COUNTS["group"]
                ptr = solute if isinstance(solute, str) else None
                SESSION.add(Groups(
                    id=COUNTS["group"], name=name, label=label, group=group, 
                    short_description=shortDesc or "", long_description=longDesc or "",
                    solute_pointer=ptr
                ))
                
                if solute and isinstance(solute, dict) and solute.get("type") == "SoluteData":
                    d = solute["data"]
                    SESSION.add(SoluteData(id=COUNTS["solute_data"], group_parent_id=COUNTS["group"], S=d.get("S"), B=d.get("B"), E=d.get("E"), L=d.get("L"), A=d.get("A"), V=d.get("V")))
                    COUNTS["solute_data"] += 1
                    
                if dataCount and isinstance(dataCount, dict) and dataCount.get("type") == "DataCountGAV":
                    d = dataCount["data"]
                    SESSION.add(DataCountGAV(id=COUNTS["count_gav"], group_parent_id=COUNTS["group"], S=d.get("S"), B=d.get("B"), E=d.get("E"), L=d.get("L"), A=d.get("A")))
                    COUNTS["count_gav"] += 1
                    
                COUNTS["group"] += 1

            def tree_spoof(tree_str):
                try:
                    for p in sketchy_conversion(tree_str):
                        SESSION.add(GroupsTree(id=COUNTS["tree"], parent_id=label_to_id.get(p[0]), child_id=label_to_id.get(p[1])))
                        COUNTS["tree"] += 1
                except Exception: pass

            env = {
                "entry": grp_entry, 
                "tree": tree_spoof,
                "SoluteData": SoluteDataSpoof, 
                "DataCountGAV": DataCountGAVSpoof,
                "ignore": "ignore",
                "forbidden": "forbidden"
            }
            try: 
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    exec(f.read_text(), env)
            except Exception as e: print(f"Error in {f.name}: {e}")

    # LIBRARIES
    tdir = Path("./original/libraries")
    if tdir.exists():
        for f in sorted(tdir.glob("*.py")):
            name = f.stem
            
            def lib_entry(*, index=None, label="", molecule=None, solute=None, solvent=None, dataCount=None, shortDesc="", longDesc="", **kwargs):
                mol = repr(molecule) if isinstance(molecule, list) else molecule
                
                if name == "solvent" or solvent:
                    SESSION.add(SolventLibraries(id=COUNTS["solvent_lib"], name=name, label=label, molecule=mol, short_description=shortDesc or "", long_description=longDesc or ""))
                    if solvent and isinstance(solvent, dict) and solvent.get("type") == "SolventData":
                        d = solvent["data"]
                        SESSION.add(SolventData(
                            id=COUNTS["solvent_data"], solvent_library_parent_id=COUNTS["solvent_lib"],
                            s_g=d.get("s_g"), b_g=d.get("b_g"), e_g=d.get("e_g"), l_g=d.get("l_g"), a_g=d.get("a_g"), c_g=d.get("c_g"),
                            s_h=d.get("s_h"), b_h=d.get("b_h"), e_h=d.get("e_h"), l_h=d.get("l_h"), a_h=d.get("a_h"), c_h=d.get("c_h"),
                            A=d.get("A"), B=d.get("B"), C=d.get("C"), D=d.get("D"), E=d.get("E"),
                            alpha=d.get("alpha"), beta=d.get("beta"), eps=d.get("eps"), n=d.get("n"), name_in_coolprop=d.get("name_in_coolprop")
                        ))
                        COUNTS["solvent_data"] += 1
                    
                    if dataCount and isinstance(dataCount, dict) and dataCount.get("type") == "DataCountSolvent":
                        d = dataCount["data"]
                        g_val, g_unit = safe_tup(d.get("dGsolvMAE"))
                        h_val, h_unit = safe_tup(d.get("dHsolvMAE"))
                        SESSION.add(DataCountSolvent(
                            id=COUNTS["count_solvent"], solvent_library_parent_id=COUNTS["solvent_lib"],
                            dGsolvCount=d.get("dGsolvCount"), dGsolvMAE_val=g_val, dGsolvMAE_unit=g_unit,
                            dHsolvCount=d.get("dHsolvCount"), dHsolvMAE_val=h_val, dHsolvMAE_unit=h_unit
                        ))
                        COUNTS["count_solvent"] += 1
                    COUNTS["solvent_lib"] += 1
                else:
                    SESSION.add(SoluteLibraries(id=COUNTS["solute_lib"], name=name, label=label, molecule=mol, short_description=shortDesc or "", long_description=longDesc or ""))
                    if solute and isinstance(solute, dict) and solute.get("type") == "SoluteData":
                        d = solute["data"]
                        SESSION.add(SoluteData(id=COUNTS["solute_data"], solute_library_parent_id=COUNTS["solute_lib"], S=d.get("S"), B=d.get("B"), E=d.get("E"), L=d.get("L"), A=d.get("A"), V=d.get("V")))
                        COUNTS["solute_data"] += 1
                    COUNTS["solute_lib"] += 1
                    
            env = {
                "entry": lib_entry, 
                "SoluteData": SoluteDataSpoof, 
                "SolventData": SolventDataSpoof,
                "DataCountGAV": DataCountGAVSpoof,
                "DataCountSolvent": DataCountSolventSpoof,
                "ignore": "ignore",
                "forbidden": "forbidden"
            }
            try: 
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    exec(f.read_text(), env)
            except Exception as e: print(f"Error in {f.name}: {e}")

    try:
        SESSION.commit()
        for view in [solute_groups_view_sql, solute_libraries_view_sql, solvent_libraries_view_sql, label_pairs_view_sql]:
            SESSION.execute(view)
        SESSION.commit()
    except Exception as e:
        print(f"Failed to commit database and create views: {e}")
        SESSION.rollback()
    SESSION.close()
