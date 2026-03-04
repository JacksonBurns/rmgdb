from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rmgdb.thermo.schema import (
    Groups, GroupsTree, ThermoLibraries, ThermoDepositories, ThermoData, Nasa, NasaPolynomial, SCHEMA_BASE
)
from rmgdb.thermo.views import (
    label_pairs_view_sql, thermo_groups_view_sql, thermo_libraries_view_sql, thermo_depositories_view_sql
)
from rmgdatabase.common.tree_str_to_pairs import sketchy_conversion

engine = create_engine("sqlite:///thermo.db", echo=False)
Session = sessionmaker(bind=engine)
SESSION = Session()
SCHEMA_BASE.metadata.create_all(engine)

def ThermoDataSpoof(**kwargs): return {"type": "ThermoData", "data": kwargs}
def NASASpoof(**kwargs): return {"type": "NASA", "data": kwargs}
def NASAPolynomialSpoof(**kwargs): return kwargs

COUNTS = {"group": 0, "lib": 0, "dep": 0, "thermo": 0, "nasa": 0, "poly": 0, "tree": 0}
LABEL_TO_ID = {None: None}
CURRENT_NAME = ""

def safe_tup(val):
    if isinstance(val, tuple): return val[0], (val[1] if len(val)>1 else None)
    return val, None

def pad(lst, size=7):
    return (list(lst) + [None]*size)[:size] if lst else [None]*size

def process_thermo(thermo, parent_col, parent_id):
    if not isinstance(thermo, dict): return
    tdata = thermo.get("data", {})
    
    if thermo["type"] == "ThermoData":
        t_val, t_unit = safe_tup(tdata.get("Tdata"))
        cp_val, cp_unit = safe_tup(tdata.get("Cpdata"))
        h_val, h_unit = safe_tup(tdata.get("H298"))
        s_val, s_unit = safe_tup(tdata.get("S298"))
        
        t_p, cp_p = pad(t_val), pad(cp_val)
        
        row = ThermoData(
            id=COUNTS["thermo"], Tdata_unit=t_unit, Cpdata_unit=cp_unit, H298=h_val, H298_unit=h_unit, S298=s_val, S298_unit=s_unit,
            Tdata_1=t_p[0], Tdata_2=t_p[1], Tdata_3=t_p[2], Tdata_4=t_p[3], Tdata_5=t_p[4], Tdata_6=t_p[5], Tdata_7=t_p[6],
            Cpdata_1=cp_p[0], Cpdata_2=cp_p[1], Cpdata_3=cp_p[2], Cpdata_4=cp_p[3], Cpdata_5=cp_p[4], Cpdata_6=cp_p[5], Cpdata_7=cp_p[6],
        )
        setattr(row, parent_col, parent_id)
        SESSION.add(row)
        COUNTS["thermo"] += 1
        
    elif thermo["type"] == "NASA":
        tmin_v, t_u = safe_tup(tdata.get("Tmin"))
        tmax_v, _ = safe_tup(tdata.get("Tmax"))
        row = Nasa(
            id=COUNTS["nasa"], Tmin=tmin_v, Tmax=tmax_v, T_unit=t_u,
            E0=safe_tup(tdata.get("E0"))[0], E0_unit=safe_tup(tdata.get("E0"))[1],
            Cp0=safe_tup(tdata.get("Cp0"))[0], Cp0_unit=safe_tup(tdata.get("Cp0"))[1],
            CpInf=safe_tup(tdata.get("CpInf"))[0], CpInf_unit=safe_tup(tdata.get("CpInf"))[1]
        )
        setattr(row, parent_col, parent_id)
        SESSION.add(row)
        
        for p in tdata.get("polynomials", []):
            c = pad(p.get("coeffs"))
            SESSION.add(NasaPolynomial(
                id=COUNTS["poly"], nasa_id=COUNTS["nasa"],
                c1=c[0], c2=c[1], c3=c[2], c4=c[3], c5=c[4], c6=c[5], c7=c[6],
                Tmin=safe_tup(p.get("Tmin"))[0], Tmax=safe_tup(p.get("Tmax"))[0], T_unit=safe_tup(p.get("Tmin"))[1]
            ))
            COUNTS["poly"] += 1
        COUNTS["nasa"] += 1

def entry_spoof(target, col, counter_key):
    def wrapper(*, index, label, molecule=None, group=None, thermo=None, shortDesc="", longDesc=""):
        kwargs = dict(id=COUNTS[counter_key], name=CURRENT_NAME, short_description=shortDesc, long_description=longDesc, label=label)
        if target == Groups:
            kwargs["group"] = group
            LABEL_TO_ID[label] = COUNTS[counter_key]
        else:
            kwargs["adjacency_list"] = molecule
            
        SESSION.add(target(**kwargs))
        process_thermo(thermo, col, COUNTS[counter_key])
        COUNTS[counter_key] += 1
    return wrapper

def tree_spoof(tree_str):
    for p in sketchy_conversion(tree_str):
        SESSION.add(GroupsTree(id=COUNTS["tree"], parent_id=LABEL_TO_ID.get(p[0]), child_id=LABEL_TO_ID.get(p[1])))
        COUNTS["tree"] += 1

def load_files(folder, spoof_func, do_tree=False):
    global CURRENT_NAME
    tdir = Path(f"./original/{folder}")
    if not tdir.exists(): return
    for f in tdir.glob("*.py"):
        CURRENT_NAME = f.stem
        env = {"entry": spoof_func, "ThermoData": ThermoDataSpoof, "NASA": NASASpoof, "NASAPolynomial": NASAPolynomialSpoof}
        if do_tree: env["tree"] = tree_spoof
        try: exec(f.read_text(), env)
        except Exception: pass

if __name__ == "__main__":
    load_files("groups", entry_spoof(Groups, "group_parent_id", "group"), do_tree=True)
    load_files("libraries", entry_spoof(ThermoLibraries, "library_parent_id", "lib"))
    load_files("depository", entry_spoof(ThermoDepositories, "depository_parent_id", "dep"))
    
    SESSION.commit()
    for view in [thermo_groups_view_sql, thermo_libraries_view_sql, thermo_depositories_view_sql, label_pairs_view_sql]:
        SESSION.execute(view)
    SESSION.commit()
    SESSION.close()
