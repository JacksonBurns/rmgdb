import sys
from pathlib import Path
import ast

# Ensure project root is on sys.path for imports
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rmgdb.transport.schema import TransportLibraries, TransportGroups, TransportGroupsTree
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class Stub:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

DB_URI = "sqlite:///transport.db"


def load_module_from_file(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_entries(file_path: Path):
    entries = []
    def entry(**kwargs):
        entries.append(kwargs)
    module_globals = {
        "entry": entry,
        "TransportData": Stub,
        "CriticalPointGroupContribution": Stub,
        "group": Stub,
    }
    code = file_path.read_text()
    exec(code, module_globals)
    return entries


def main():
    engine = create_engine(DB_URI)
    TransportLibraries.metadata.create_all(engine)
    TransportGroups.metadata.create_all(engine)
    TransportGroupsTree.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    base_dir = Path("data/rmgdatabase/transport")
    libs_dir = base_dir / "libraries"
    groups_dir = base_dir / "groups"

    for lib_file in libs_dir.glob("*.py"):
        entries = parse_entries(lib_file)
        for e in entries:
            lib = TransportLibraries(
                name=e.get("name"),
                short_description=e.get("shortDesc"),
                long_description=e.get("longDesc"),
                label=e.get("label"),
                molecule=e.get("molecule"),
                shape_index=e.get("transport", {}).get("shapeIndex"),
                epsilon=e.get("transport", {}).get("epsilon", (None, None))[0],
                epsilon_unit=e.get("transport", {}).get("epsilon", (None, None))[1],
                sigma=e.get("transport", {}).get("sigma", (None, None))[0],
                sigma_unit=e.get("transport", {}).get("sigma", (None, None))[1],
                dipole_moment=e.get("transport", {}).get("dipoleMoment", (None, None))[0],
                dipole_moment_unit=e.get("transport", {}).get("dipoleMoment", (None, None))[1],
                polarizability=e.get("transport", {}).get("polarizability", (None, None))[0],
                polarizability_unit=e.get("transport", {}).get("polarizability", (None, None))[1],
                rotrelaxcollnum=e.get("transport", {}).get("rotrelaxcollnum"),
            )
            session.add(lib)

    for grp_file in groups_dir.glob("*.py"):
        entries = parse_entries(grp_file)
        for e in entries:
            grp = TransportGroups(
                name=e.get("name"),
                short_description=e.get("shortDesc"),
                long_description=e.get("longDesc"),
                label=e.get("label"),
                group=e.get("group"),
                tc=e.get("transportGroup", {}).get("Tc"),
                pc=e.get("transportGroup", {}).get("Pc"),
                vc=e.get("transportGroup", {}).get("Vc"),
                tb=e.get("transportGroup", {}).get("Tb"),
                structure_index=e.get("transportGroup", {}).get("structureIndex"),
            )
            session.add(grp)

    session.commit()
    print("Transport database built.")

if __name__ == "__main__":
    main()
