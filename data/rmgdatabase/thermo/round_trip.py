import yaml
import pandas as pd
from tqdm import tqdm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

from rmgdb.thermo.schema import (
    SCHEMA_BASE, Groups, GroupsTree, ThermoLibraries, ThermoDepositories, 
    ThermoData, Nasa, NasaPolynomial
)
from rmgdb.thermo.views import (
    label_pairs_view_sql, thermo_groups_view_sql, 
    thermo_libraries_view_sql, thermo_depositories_view_sql
)

yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str
repr_str = lambda dumper, data: (
    dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|") if "\n" in data else dumper.org_represent_str(data)
)
yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)

def clean_none(d):
    return {k: v for k, v in d.items() if v is not None and not pd.isna(v)}

def pad_list(lst, size=7):
    if lst is None:
        return [None] * size
    res = list(lst)
    while len(res) < size:
        res.append(None)
    return res

def reconstruct_thermo(parent_col, parent_id, session):
    tds = session.query(ThermoData).filter(getattr(ThermoData, parent_col) == parent_id).all()
    if tds:
        td = tds[0]
        Tdata = [getattr(td, f"Tdata_{i}") for i in range(1, 8)]
        Tdata = [x for x in Tdata if x is not None]
        
        Cpdata = [getattr(td, f"Cpdata_{i}") for i in range(1, 8)]
        Cpdata = [x for x in Cpdata if x is not None]
        
        Cpdata_unc = [getattr(td, f"Cpdata_unc_{i}") for i in range(1, 8)]
        Cpdata_unc = [x for x in Cpdata_unc if x is not None]
        
        out = {"type": "ThermoData"}
        out["Tdata"] = [Tdata, td.Tdata_unit] if Tdata else None
        
        if Cpdata_unc:
            out["Cpdata"] = [Cpdata, td.Cpdata_unit, "+|-", Cpdata_unc]
        else:
            out["Cpdata"] = [Cpdata, td.Cpdata_unit] if Cpdata else None
            
        if td.H298_unc is not None:
            out["H298"] = [td.H298, td.H298_unit, "+|-", td.H298_unc]
        else:
            out["H298"] = [td.H298, td.H298_unit] if pd.notna(td.H298) else None
            
        if td.S298_unc is not None:
            out["S298"] = [td.S298, td.S298_unit, "+|-", td.S298_unc]
        else:
            out["S298"] = [td.S298, td.S298_unit] if pd.notna(td.S298) else None
            
        return clean_none(out)
        
    nasas = session.query(Nasa).filter(getattr(Nasa, parent_col) == parent_id).all()
    if nasas:
        n = nasas[0]
        out = {"type": "NASA"}
        out["Tmin"] = [n.Tmin, n.T_unit] if pd.notna(n.Tmin) else None
        out["Tmax"] = [n.Tmax, n.T_unit] if pd.notna(n.Tmax) else None
        out["E0"] = [n.E0, n.E0_unit] if pd.notna(n.E0) else None
        out["Cp0"] = [n.Cp0, n.Cp0_unit] if pd.notna(n.Cp0) else None
        out["CpInf"] = [n.CpInf, n.CpInf_unit] if pd.notna(n.CpInf) else None
        
        polys = session.query(NasaPolynomial).filter(NasaPolynomial.nasa_id == n.id).all()
        poly_list = []
        for p in polys:
            c = [getattr(p, f"c{i}") for i in range(1, 8)]
            poly_list.append({
                "coeffs": [x for x in c if pd.notna(x)],
                "Tmin": [p.Tmin, p.T_unit] if pd.notna(p.Tmin) else None,
                "Tmax": [p.Tmax, p.T_unit] if pd.notna(p.Tmax) else None,
            })
        out["polynomials"] = poly_list
        return clean_none(out)
    return None

def dump_db():
    Path("yml/libraries").mkdir(parents=True, exist_ok=True)
    Path("yml/groups").mkdir(parents=True, exist_ok=True)
    Path("yml/depository").mkdir(parents=True, exist_ok=True)
    
    engine = create_engine("sqlite:///thermo.db", echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Libraries
    all_libs = pd.read_sql("SELECT * FROM thermo_libraries_view", engine)
    for lib_name, lib_df in tqdm(all_libs.groupby("name"), desc="Generating libraries"):
        all_rows = []
        for _, row in lib_df.iterrows():
            formatted_dict = dict(
                label=row.label,
                short_description=row.short_description,
                long_description=row.long_description,
                adjacency_list=row.adjacency_list,
            )
            th = reconstruct_thermo("library_parent_id", row.id, session)
            if th: formatted_dict["thermo"] = th
            all_rows.append(clean_none(formatted_dict))
        with open(f"yml/libraries/{lib_name}.yml", "w") as f:
            yaml.dump_all(all_rows, f, yaml.SafeDumper, sort_keys=False)
            
    # Depositories
    all_deps = pd.read_sql("SELECT * FROM thermo_depositories_view", engine)
    for dep_name, dep_df in tqdm(all_deps.groupby("name"), desc="Generating depositories"):
        all_rows = []
        for _, row in dep_df.iterrows():
            formatted_dict = dict(
                label=row.label,
                short_description=row.short_description,
                long_description=row.long_description,
                adjacency_list=row.adjacency_list,
            )
            th = reconstruct_thermo("depository_parent_id", row.id, session)
            if th: formatted_dict["thermo"] = th
            all_rows.append(clean_none(formatted_dict))
        with open(f"yml/depository/{dep_name}.yml", "w") as f:
            yaml.dump_all(all_rows, f, yaml.SafeDumper, sort_keys=False)
            
    # Groups
    all_groups = pd.read_sql("SELECT * FROM thermo_groups_view", engine)
    for grp_name, grp_df in tqdm(all_groups.groupby("name"), desc="Generating groups"):
        all_rows = []
        for _, row in grp_df.iterrows():
            group_pairs = pd.read_sql(
                f"SELECT child_label from label_pairs_view WHERE label_pairs_view.parent_label = '{row.label}'",
                engine,
            )
            formatted_dict = dict(
                label=row.label,
                children=group_pairs["child_label"].to_list() if not group_pairs.empty else [],
                short_description=row.short_description,
                long_description=row.long_description,
                group=row["group"],
            )
            
            if pd.notna(row.thermo_pointer) and row.thermo_pointer:
                formatted_dict["thermo"] = row.thermo_pointer
            else:
                th = reconstruct_thermo("group_parent_id", row.id, session)
                if th: formatted_dict["thermo"] = th
                    
            all_rows.append(clean_none(formatted_dict))
        with open(f"yml/groups/{grp_name}.yml", "w") as f:
            yaml.dump_all(all_rows, f, yaml.SafeDumper, sort_keys=False)
            
    session.close()

THERMO_DATA_COUNT = 0
NASA_COUNT = 0
NASA_POLY_COUNT = 0

def parse_thermo_dict(th_dict, parent_col, parent_id, session):
    global THERMO_DATA_COUNT, NASA_COUNT, NASA_POLY_COUNT
    
    ttype = th_dict.get("type")
    if ttype == "ThermoData":
        Tdata = pad_list(th_dict.get("Tdata", [None, None])[0], 7)
        T_unit = th_dict.get("Tdata", [None, None])[1]
        
        Cpdata_list = th_dict.get("Cpdata", [None, None])
        Cp_val = pad_list(Cpdata_list[0], 7)
        Cp_unit = Cpdata_list[1]
        Cp_unc = pad_list(Cpdata_list[3] if len(Cpdata_list) >= 4 else None, 7)
        
        H298_list = th_dict.get("H298", [None, None])
        H_val, H_unit = H298_list[0], H298_list[1]
        H_unc = H298_list[3] if len(H298_list) >= 4 else None
        
        S298_list = th_dict.get("S298", [None, None])
        S_val, S_unit = S298_list[0], S298_list[1]
        S_unc = S298_list[3] if len(S298_list) >= 4 else None
        
        row = ThermoData(
            id=THERMO_DATA_COUNT,
            Tdata_1=Tdata[0], Tdata_2=Tdata[1], Tdata_3=Tdata[2], Tdata_4=Tdata[3], Tdata_5=Tdata[4], Tdata_6=Tdata[5], Tdata_7=Tdata[6], Tdata_unit=T_unit,
            Cpdata_1=Cp_val[0], Cpdata_2=Cp_val[1], Cpdata_3=Cp_val[2], Cpdata_4=Cp_val[3], Cpdata_5=Cp_val[4], Cpdata_6=Cp_val[5], Cpdata_7=Cp_val[6], Cpdata_unit=Cp_unit,
            Cpdata_unc_1=Cp_unc[0], Cpdata_unc_2=Cp_unc[1], Cpdata_unc_3=Cp_unc[2], Cpdata_unc_4=Cp_unc[3], Cpdata_unc_5=Cp_unc[4], Cpdata_unc_6=Cp_unc[5], Cpdata_unc_7=Cp_unc[6],
            H298=H_val, H298_unit=H_unit, H298_unc=H_unc,
            S298=S_val, S298_unit=S_unit, S298_unc=S_unc
        )
        setattr(row, parent_col, parent_id)
        session.add(row)
        THERMO_DATA_COUNT += 1
        
    elif ttype == "NASA":
        row = Nasa(
            id=NASA_COUNT,
            Tmin=th_dict.get("Tmin", [None])[0], Tmax=th_dict.get("Tmax", [None])[0], T_unit=th_dict.get("Tmin", [None, None])[1],
            E0=th_dict.get("E0", [None])[0], E0_unit=th_dict.get("E0", [None, None])[1],
            Cp0=th_dict.get("Cp0", [None])[0], Cp0_unit=th_dict.get("Cp0", [None, None])[1],
            CpInf=th_dict.get("CpInf", [None])[0], CpInf_unit=th_dict.get("CpInf", [None, None])[1],
        )
        setattr(row, parent_col, parent_id)
        session.add(row)
        
        for poly in th_dict.get("polynomials", []):
            c_pad = pad_list(poly.get("coeffs", []), 7)
            p_row = NasaPolynomial(
                id=NASA_POLY_COUNT, nasa_id=NASA_COUNT,
                c1=c_pad[0], c2=c_pad[1], c3=c_pad[2], c4=c_pad[3], c5=c_pad[4], c6=c_pad[5], c7=c_pad[6],
                Tmin=poly.get("Tmin", [None])[0], Tmax=poly.get("Tmax", [None])[0], T_unit=poly.get("Tmin", [None, None])[1]
            )
            session.add(p_row)
            NASA_POLY_COUNT += 1
        NASA_COUNT += 1

def gen_db():
    engine = create_engine("sqlite:///thermo.db", echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    SCHEMA_BASE.metadata.create_all(engine)

    lib_counter = 0
    dep_counter = 0
    group_counter = 0
    tree_count = 0
    
    # 1. Libraries
    if Path("yml/libraries").exists():
        for f in tqdm(Path("yml/libraries").glob("*.yml"), desc="Loading libraries"):
            with open(f, "r") as fl:
                for row in yaml.safe_load_all(fl):
                    new_row = ThermoLibraries(
                        id=lib_counter, name=f.stem, short_description=row.get("short_description", ""),
                        long_description=row.get("long_description", ""), label=row["label"],
                        adjacency_list=row.get("adjacency_list", "")
                    )
                    session.add(new_row)
                    if "thermo" in row and isinstance(row["thermo"], dict):
                        parse_thermo_dict(row["thermo"], "library_parent_id", lib_counter, session)
                    lib_counter += 1

    # 2. Depositories
    if Path("yml/depository").exists():
        for f in tqdm(Path("yml/depository").glob("*.yml"), desc="Loading depositories"):
            with open(f, "r") as fl:
                for row in yaml.safe_load_all(fl):
                    new_row = ThermoDepositories(
                        id=dep_counter, name=f.stem, short_description=row.get("short_description", ""),
                        long_description=row.get("long_description", ""), label=row["label"],
                        adjacency_list=row.get("adjacency_list", "")
                    )
                    session.add(new_row)
                    if "thermo" in row and isinstance(row["thermo"], dict):
                        parse_thermo_dict(row["thermo"], "depository_parent_id", dep_counter, session)
                    dep_counter += 1

    # 3. Groups
    label_to_id = {None: None}
    if Path("yml/groups").exists():
        for f in tqdm(Path("yml/groups").glob("*.yml"), desc="Loading groups"):
            with open(f, "r") as fl:
                all_rows = list(yaml.safe_load_all(fl))
                for row in all_rows:
                    label_to_id[row["label"]] = group_counter
                    new_row = Groups(
                        id=group_counter, name=f.stem, short_description=row.get("short_description", ""),
                        long_description=row.get("long_description", ""), label=row["label"],
                        group=row.get("group", ""),
                        thermo_pointer=row["thermo"] if isinstance(row.get("thermo"), str) else None
                    )
                    session.add(new_row)
                    if "thermo" in row and isinstance(row["thermo"], dict):
                        parse_thermo_dict(row["thermo"], "group_parent_id", group_counter, session)
                    group_counter += 1

                for row in all_rows:
                    for child_label in row.get("children", []):
                        new_tree = GroupsTree(
                            id=tree_count,
                            parent_id=label_to_id[row["label"]],
                            child_id=label_to_id[child_label],
                        )
                        session.add(new_tree)
                        tree_count += 1

    try: session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")

    session.execute(thermo_groups_view_sql)
    session.execute(thermo_libraries_view_sql)
    session.execute(thermo_depositories_view_sql)
    session.execute(label_pairs_view_sql)
    session.commit()
    session.close()

if __name__ == "__main__":
    dump_db()
    Path("thermo.db").rename("old.db")
    gen_db()
