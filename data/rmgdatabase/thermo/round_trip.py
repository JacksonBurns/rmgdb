import yaml
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rmgdb.thermo.schema import (
    SCHEMA_BASE, Groups, GroupsTree, ThermoLibraries, ThermoDepositories, 
    ThermoData, Nasa, NasaPolynomial
)
from rmgdb.thermo.views import (
    label_pairs_view_sql, thermo_groups_view_sql, 
    thermo_libraries_view_sql, thermo_depositories_view_sql
)

yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str
repr_str = lambda dumper, data: dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|") if "\n" in data else dumper.org_represent_str(data)
yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)

def clean_dict(d):
    cleaned = {}
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, float) and pd.isna(v):
            continue
        cleaned[k] = v
    return cleaned

def extract_thermo(col, pid, session):
    td = session.query(ThermoData).filter(getattr(ThermoData, col) == pid).first()
    if td:
        t_arr = [x for x in [td.Tdata_1, td.Tdata_2, td.Tdata_3, td.Tdata_4, td.Tdata_5, td.Tdata_6, td.Tdata_7] if pd.notna(x)]
        cp_arr = [x for x in [td.Cpdata_1, td.Cpdata_2, td.Cpdata_3, td.Cpdata_4, td.Cpdata_5, td.Cpdata_6, td.Cpdata_7] if pd.notna(x)]
        return clean_dict({
            "type": "ThermoData",
            "Tdata": [t_arr, td.Tdata_unit] if t_arr else None,
            "Cpdata": [cp_arr, td.Cpdata_unit] if cp_arr else None,
            "H298": [td.H298, td.H298_unit] if pd.notna(td.H298) else None,
            "S298": [td.S298, td.S298_unit] if pd.notna(td.S298) else None
        })
    
    nasa = session.query(Nasa).filter(getattr(Nasa, col) == pid).first()
    if nasa:
        polys = []
        for p in session.query(NasaPolynomial).filter(NasaPolynomial.nasa_id == nasa.id).all():
            c_arr = [x for x in [p.c1, p.c2, p.c3, p.c4, p.c5, p.c6, p.c7] if pd.notna(x)]
            polys.append(clean_dict({
                "coeffs": c_arr,
                "Tmin": [p.Tmin, p.T_unit] if pd.notna(p.Tmin) else None,
                "Tmax": [p.Tmax, p.T_unit] if pd.notna(p.Tmax) else None
            }))
        return clean_dict({
            "type": "NASA",
            "Tmin": [nasa.Tmin, nasa.T_unit] if pd.notna(nasa.Tmin) else None,
            "Tmax": [nasa.Tmax, nasa.T_unit] if pd.notna(nasa.Tmax) else None,
            "E0": [nasa.E0, nasa.E0_unit] if pd.notna(nasa.E0) else None,
            "polynomials": polys
        })
    return None

def dump_db():
    for f in ["yml/libraries", "yml/depository", "yml/groups"]: Path(f).mkdir(parents=True, exist_ok=True)
    engine = create_engine("sqlite:///thermo.db", echo=False)
    session = sessionmaker(bind=engine)()

    for table, view, key, col in [
        ("libraries", "thermo_libraries_view", "adjacency_list", "library_parent_id"),
        ("depository", "thermo_depositories_view", "adjacency_list", "depository_parent_id"),
        ("groups", "thermo_groups_view", "group", "group_parent_id")
    ]:
        df = pd.read_sql(f"SELECT * FROM {view}", engine)
        for name, grp in df.groupby("name"):
            rows = []
            for _, r in grp.iterrows():
                d = clean_dict({"label": r.label, "short_description": r.short_description, "long_description": r.long_description, key: getattr(r, key)})
                if table == "groups":
                    ch = pd.read_sql(f"SELECT child_label FROM label_pairs_view WHERE parent_label='{r.label}'", engine)
                    d["children"] = ch["child_label"].tolist() if not ch.empty else []
                th = extract_thermo(col, r.id, session)
                if th: d["thermo"] = th
                rows.append(d)
            if rows:
                with open(f"yml/{table}/{name}.yml", "w") as f: yaml.dump_all(rows, f, yaml.SafeDumper, sort_keys=False)

def pad_list(lst, size=7):
    return (list(lst) + [None]*size)[:size] if lst else [None]*size

def insert_thermo(th_dict, parent_col, parent_id, session, counts):
    ttype = th_dict.get("type")
    if ttype == "ThermoData":
        t_val = pad_list(th_dict.get("Tdata", [[]])[0], 7)
        t_unit = th_dict.get("Tdata", [None, None])[1] if th_dict.get("Tdata") else None
        
        cp_val = pad_list(th_dict.get("Cpdata", [[]])[0], 7)
        cp_unit = th_dict.get("Cpdata", [None, None])[1] if th_dict.get("Cpdata") else None
        
        h_val = th_dict.get("H298", [None])[0]
        h_unit = th_dict.get("H298", [None, None])[1] if th_dict.get("H298") else None
        
        s_val = th_dict.get("S298", [None])[0]
        s_unit = th_dict.get("S298", [None, None])[1] if th_dict.get("S298") else None
        
        row = ThermoData(
            id=counts["thermo"], Tdata_unit=t_unit, Cpdata_unit=cp_unit, H298=h_val, H298_unit=h_unit, S298=s_val, S298_unit=s_unit,
            Tdata_1=t_val[0], Tdata_2=t_val[1], Tdata_3=t_val[2], Tdata_4=t_val[3], Tdata_5=t_val[4], Tdata_6=t_val[5], Tdata_7=t_val[6],
            Cpdata_1=cp_val[0], Cpdata_2=cp_val[1], Cpdata_3=cp_val[2], Cpdata_4=cp_val[3], Cpdata_5=cp_val[4], Cpdata_6=cp_val[5], Cpdata_7=cp_val[6],
        )
        setattr(row, parent_col, parent_id)
        session.add(row)
        counts["thermo"] += 1
        
    elif ttype == "NASA":
        tmin_v = th_dict.get("Tmin", [None])[0]
        tmax_v = th_dict.get("Tmax", [None])[0]
        t_u = th_dict.get("Tmin", [None, None])[1] if th_dict.get("Tmin") else None
        e0_v = th_dict.get("E0", [None])[0]
        e0_u = th_dict.get("E0", [None, None])[1] if th_dict.get("E0") else None
        
        row = Nasa(
            id=counts["nasa"], Tmin=tmin_v, Tmax=tmax_v, T_unit=t_u, E0=e0_v, E0_unit=e0_u
        )
        setattr(row, parent_col, parent_id)
        session.add(row)
        
        for poly in th_dict.get("polynomials", []):
            c = pad_list(poly.get("coeffs", []), 7)
            ptmin = poly.get("Tmin", [None])[0]
            ptmax = poly.get("Tmax", [None])[0]
            ptu = poly.get("Tmin", [None, None])[1] if poly.get("Tmin") else None
            
            p_row = NasaPolynomial(
                id=counts["poly"], nasa_id=row.id,
                c1=c[0], c2=c[1], c3=c[2], c4=c[3], c5=c[4], c6=c[5], c7=c[6],
                Tmin=ptmin, Tmax=ptmax, T_unit=ptu
            )
            session.add(p_row)
            counts["poly"] += 1
            
        counts["nasa"] += 1

def gen_db():
    engine = create_engine("sqlite:///thermo.db", echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    SCHEMA_BASE.metadata.create_all(engine)

    counts = {"lib": 0, "dep": 0, "group": 0, "thermo": 0, "nasa": 0, "poly": 0, "tree": 0}
    label_to_id = {}

    if Path("yml/libraries").exists():
        for f in Path("yml/libraries").glob("*.yml"):
            with open(f, "r") as fl:
                for row in yaml.safe_load_all(fl):
                    session.add(ThermoLibraries(
                        id=counts["lib"], name=f.stem, label=row["label"], adjacency_list=row.get("adjacency_list", ""),
                        short_description=row.get("short_description", ""), long_description=row.get("long_description", "")
                    ))
                    if "thermo" in row and isinstance(row["thermo"], dict):
                        insert_thermo(row["thermo"], "library_parent_id", counts["lib"], session, counts)
                    counts["lib"] += 1

    if Path("yml/depository").exists():
        for f in Path("yml/depository").glob("*.yml"):
            with open(f, "r") as fl:
                for row in yaml.safe_load_all(fl):
                    session.add(ThermoDepositories(
                        id=counts["dep"], name=f.stem, label=row["label"], adjacency_list=row.get("adjacency_list", ""),
                        short_description=row.get("short_description", ""), long_description=row.get("long_description", "")
                    ))
                    if "thermo" in row and isinstance(row["thermo"], dict):
                        insert_thermo(row["thermo"], "depository_parent_id", counts["dep"], session, counts)
                    counts["dep"] += 1

    if Path("yml/groups").exists():
        for f in Path("yml/groups").glob("*.yml"):
            with open(f, "r") as fl:
                all_rows = list(yaml.safe_load_all(fl))
                for row in all_rows:
                    label_to_id[row["label"]] = counts["group"]
                    session.add(Groups(
                        id=counts["group"], name=f.stem, label=row["label"], group=row.get("group", ""),
                        short_description=row.get("short_description", ""), long_description=row.get("long_description", "")
                    ))
                    if "thermo" in row and isinstance(row["thermo"], dict):
                        insert_thermo(row["thermo"], "group_parent_id", counts["group"], session, counts)
                    counts["group"] += 1

                for row in all_rows:
                    for child in row.get("children", []):
                        if child in label_to_id:
                            session.add(GroupsTree(
                                id=counts["tree"], parent_id=label_to_id[row["label"]], child_id=label_to_id[child]
                            ))
                            counts["tree"] += 1

    try:
        session.commit()
        session.execute(thermo_groups_view_sql)
        session.execute(thermo_libraries_view_sql)
        session.execute(thermo_depositories_view_sql)
        session.execute(label_pairs_view_sql)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error during gen_db commit: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    dump_db()
    Path("thermo.db").rename("old.db")
    gen_db()
