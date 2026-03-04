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

LABEL_TO_DB_ID = {None: None}

# SPOOFERS FOR RMG CLASSES
def ThermoDataSpoof(**kwargs):
    return {"type": "ThermoData", "data": kwargs}

def NASASpoof(**kwargs):
    return {"type": "NASA", "data": kwargs}

def NASAPolynomialSpoof(**kwargs):
    return kwargs

def WilhoitSpoof(**kwargs):
    return {"type": "Wilhoit", "data": kwargs}
    
def HarmonicOscillatorSpoof(**kwargs):
    return {"type": "HarmonicOscillator", "data": kwargs}

ENTRY_COUNT = 0
LIB_ENTRY_COUNT = 0
DEP_ENTRY_COUNT = 0
THERMO_DATA_COUNT = 0
NASA_COUNT = 0
NASA_POLY_COUNT = 0
TREE_PAIRS_COUNT = 0
CURRENT_NAME = ""

def parse_val_unc(tup):
    if isinstance(tup, tuple):
        val = tup[0]
        unit = tup[1] if len(tup) > 1 else None
        unc = tup[3] if len(tup) >= 4 else None
        return val, unit, unc
    return tup, None, None

def pad_list(lst, size=7):
    if lst is None:
        return [None] * size
    res = list(lst)
    while len(res) < size:
        res.append(None)
    return res

def process_thermo(thermo_obj, parent_col, parent_id):
    global THERMO_DATA_COUNT, NASA_COUNT, NASA_POLY_COUNT
    if not isinstance(thermo_obj, dict):
        return
        
    ttype = thermo_obj.get("type")
    tdata = thermo_obj.get("data", {})
    
    if ttype == "ThermoData":
        T_val, T_unit, _ = parse_val_unc(tdata.get("Tdata"))
        Cp_val, Cp_unit, Cp_unc = parse_val_unc(tdata.get("Cpdata"))
        H_val, H_unit, H_unc = parse_val_unc(tdata.get("H298"))
        S_val, S_unit, S_unc = parse_val_unc(tdata.get("S298"))
        
        T_pad = pad_list(T_val)
        Cp_pad = pad_list(Cp_val)
        Cp_unc_pad = pad_list(Cp_unc)
        
        row = ThermoData(
            id=THERMO_DATA_COUNT,
            Tdata_1=T_pad[0], Tdata_2=T_pad[1], Tdata_3=T_pad[2], Tdata_4=T_pad[3], Tdata_5=T_pad[4], Tdata_6=T_pad[5], Tdata_7=T_pad[6],
            Tdata_unit=T_unit,
            Cpdata_1=Cp_pad[0], Cpdata_2=Cp_pad[1], Cpdata_3=Cp_pad[2], Cpdata_4=Cp_pad[3], Cpdata_5=Cp_pad[4], Cpdata_6=Cp_pad[5], Cpdata_7=Cp_pad[6],
            Cpdata_unit=Cp_unit,
            Cpdata_unc_1=Cp_unc_pad[0], Cpdata_unc_2=Cp_unc_pad[1], Cpdata_unc_3=Cp_unc_pad[2], Cpdata_unc_4=Cp_unc_pad[3], Cpdata_unc_5=Cp_unc_pad[4], Cpdata_unc_6=Cp_unc_pad[5], Cpdata_unc_7=Cp_unc_pad[6],
            H298=H_val, H298_unit=H_unit, H298_unc=H_unc,
            S298=S_val, S298_unit=S_unit, S298_unc=S_unc,
        )
        setattr(row, parent_col, parent_id)
        SESSION.add(row)
        THERMO_DATA_COUNT += 1
        
    elif ttype == "NASA":
        Tmin_val, T_unit, _ = parse_val_unc(tdata.get("Tmin"))
        Tmax_val, _, _ = parse_val_unc(tdata.get("Tmax"))
        E0_val, E0_unit, _ = parse_val_unc(tdata.get("E0"))
        Cp0_val, Cp0_unit, _ = parse_val_unc(tdata.get("Cp0"))
        CpInf_val, CpInf_unit, _ = parse_val_unc(tdata.get("CpInf"))
        
        nasa_row = Nasa(
            id=NASA_COUNT,
            Tmin=Tmin_val, Tmax=Tmax_val, T_unit=T_unit,
            E0=E0_val, E0_unit=E0_unit,
            Cp0=Cp0_val, Cp0_unit=Cp0_unit,
            CpInf=CpInf_val, CpInf_unit=CpInf_unit,
        )
        setattr(nasa_row, parent_col, parent_id)
        SESSION.add(nasa_row)
        
        for poly in tdata.get("polynomials", []):
            c_pad = pad_list(poly.get("coeffs", []), size=7)
            ptmin, ptunit, _ = parse_val_unc(poly.get("Tmin"))
            ptmax, _, _ = parse_val_unc(poly.get("Tmax"))
            p_row = NasaPolynomial(
                id=NASA_POLY_COUNT,
                nasa_id=NASA_COUNT,
                c1=c_pad[0], c2=c_pad[1], c3=c_pad[2], c4=c_pad[3], c5=c_pad[4], c6=c_pad[5], c7=c_pad[6],
                Tmin=ptmin, Tmax=ptmax, T_unit=ptunit
            )
            SESSION.add(p_row)
            NASA_POLY_COUNT += 1
            
        NASA_COUNT += 1

def entry_group_spoof(*, index, label, group, thermo=None, shortDesc="", longDesc=""):
    global ENTRY_COUNT, CURRENT_NAME
    ptr = thermo if isinstance(thermo, str) else None
    
    row = Groups(
        id=ENTRY_COUNT,
        name=CURRENT_NAME,
        short_description=shortDesc,
        long_description=longDesc,
        label=label,
        group=group,
        thermo_pointer=ptr
    )
    LABEL_TO_DB_ID[label] = ENTRY_COUNT
    SESSION.add(row)
    
    if not isinstance(thermo, str):
        process_thermo(thermo, "group_parent_id", ENTRY_COUNT)
    ENTRY_COUNT += 1

def tree_spoof(tree_str):
    global TREE_PAIRS_COUNT
    pairs = sketchy_conversion(tree_str)
    for pair in pairs:
        row = GroupsTree(
            id=TREE_PAIRS_COUNT,
            parent_id=LABEL_TO_DB_ID.get(pair[0]),
            child_id=LABEL_TO_DB_ID.get(pair[1]),
        )
        SESSION.add(row)
        TREE_PAIRS_COUNT += 1

def entry_library_spoof(*, index, label, molecule, thermo=None, shortDesc="", longDesc=""):
    global LIB_ENTRY_COUNT, CURRENT_NAME
    row = ThermoLibraries(
        id=LIB_ENTRY_COUNT, name=CURRENT_NAME,
        short_description=shortDesc, long_description=longDesc,
        label=label, adjacency_list=molecule,
    )
    SESSION.add(row)
    process_thermo(thermo, "library_parent_id", LIB_ENTRY_COUNT)
    LIB_ENTRY_COUNT += 1

def entry_depository_spoof(*, index, label, molecule, thermo=None, shortDesc="", longDesc=""):
    global DEP_ENTRY_COUNT, CURRENT_NAME
    row = ThermoDepositories(
        id=DEP_ENTRY_COUNT, name=CURRENT_NAME,
        short_description=shortDesc, long_description=longDesc,
        label=label, adjacency_list=molecule,
    )
    SESSION.add(row)
    process_thermo(thermo, "depository_parent_id", DEP_ENTRY_COUNT)
    DEP_ENTRY_COUNT += 1


base_dir = Path("./original")

def load_files(folder, spoof_func, do_tree=False):
    global CURRENT_NAME
    target_dir = base_dir / folder
    if not target_dir.exists():
        return
    for f in target_dir.glob("*.py"):
        CURRENT_NAME = f.stem
        env = {
            "entry": spoof_func,
            "ThermoData": ThermoDataSpoof,
            "NASA": NASASpoof,
            "NASAPolynomial": NASAPolynomialSpoof,
            "Wilhoit": WilhoitSpoof,
            "HarmonicOscillator": HarmonicOscillatorSpoof,
        }
        if do_tree:
            env["tree"] = tree_spoof
        try:
            exec(f.read_text(), env)
        except Exception:
            pass

if __name__ == "__main__":
    load_files("groups", entry_group_spoof, do_tree=True)
    load_files("libraries", entry_library_spoof)
    load_files("depository", entry_depository_spoof)

    try:
        SESSION.commit()
    except Exception as e:
        SESSION.rollback()
        print(f"Error: {e}")

    SESSION.execute(thermo_groups_view_sql)
    SESSION.execute(thermo_libraries_view_sql)
    SESSION.execute(thermo_depositories_view_sql)
    SESSION.execute(label_pairs_view_sql)
    SESSION.commit()
    SESSION.close()
