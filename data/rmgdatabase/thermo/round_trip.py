import yaml
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rmgdb.thermo.schema import ThermoData, Nasa, NasaPolynomial

yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str
repr_str = lambda dumper, data: dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|") if "\n" in data else dumper.org_represent_str(data)
yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)

def clean_dict(d):
    cleaned = {}
    for k, v in d.items():
        if v is None:
            continue
        # Only use pd.isna on scalar floats, otherwise it crashes on lists
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
            with open(f"yml/{table}/{name}.yml", "w") as f: yaml.dump_all(rows, f, yaml.SafeDumper, sort_keys=False)

if __name__ == "__main__":
    dump_db()
