import sys
from pathlib import Path
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Resolve the project root relative to this script
ROOT = Path(__file__).resolve().parents[2]
# Import the schema after ensuring path resolution
from rmgdb.transport.schema import TransportLibraries, TransportGroups

DB_URI = "sqlite:///transport.db"

if __name__ == "__main__":
    engine = create_engine(DB_URI)
    # Create tables if they don't exist
    TransportLibraries.__table__.create(engine, checkfirst=True)
    TransportGroups.__table__.create(engine, checkfirst=True)

    Session = sessionmaker(bind=engine)
    session = Session()

    libs = session.query(TransportLibraries).all()
    groups = session.query(TransportGroups).all()

    out = {"libraries": [], "groups": []}

    for lib in libs:
        out["libraries"].append({
            "name": lib.name,
            "shortDesc": lib.short_description,
            "longDesc": lib.long_description,
            "label": lib.label,
            "molecule": lib.molecule,
            "transport": {
                "shapeIndex": lib.shape_index,
                "epsilon": {"value": lib.epsilon, "unit": lib.epsilon_unit},
                "sigma": {"value": lib.sigma, "unit": lib.sigma_unit},
                "dipoleMoment": {"value": lib.dipole_moment, "unit": lib.dipole_moment_unit},
                "polarizability": {"value": lib.polarizability, "unit": lib.polarizability_unit},
                "rotrelaxcollnum": lib.rotrelaxcollnum,
            },
            "shortDesc": lib.short_description,
        })

    for grp in groups:
        out["groups"].append({
            "name": grp.name,
            "shortDesc": grp.short_description,
            "longDesc": grp.long_description,
            "label": grp.label,
            "group": grp.group,
            "transportGroup": {
                "Tc": grp.tc,
                "Pc": grp.pc,
                "Vc": grp.vc,
                "Tb": grp.tb,
                "structureIndex": grp.structure_index,
            },
        })

    out_path = Path("transport.yml")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump(out, sort_keys=False))
    print("Exported to transport.yml")
