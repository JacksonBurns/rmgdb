import sys
from pathlib import Path
import importlib.util
import logging

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from rmgdb.transport.schema import TransportLibraries, TransportGroups, TransportGroupsTree
from rmgdatabase.common.tree_str_to_pairs import sketchy_conversion
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_URI = "sqlite:///transport.db"

LABEL_TO_DB_ID = {None: None}  # None: None for root/leaf nodes
ENTRY_COUNT = 1  # Start from 1 to avoid conflicts with None

class Stub:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def parse_entry(file_path: Path):
    entries = []
    def entry(**kwargs):
        entries.append(kwargs)
        logging.info(f"Captured entry from {file_path.name}: {kwargs.get('label', 'n/a')}")
    globals_ = {
        "entry": entry,
        "TransportData": Stub,
        "CriticalPointGroupContribution": Stub,
        "group": Stub,
        "tree": Stub,
    }
    exec(file_path.read_text(), globals_)
    return entries


def main():
    logging.info("Starting build process")
    engine = create_engine(DB_URI)
    TransportLibraries.metadata.create_all(engine)
    TransportGroups.metadata.create_all(engine)
    TransportGroupsTree.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    base_dir = Path(__file__).resolve().parent / "original"
    libs_dir = base_dir / "libraries"
    groups_dir = base_dir / "groups"

    for lib_file in libs_dir.glob("*.py"):
        entries = parse_entry(lib_file)
        for e in entries[0:-1]:
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
            LABEL_TO_DB_ID[e.get("label")] = ENTRY_COUNT
            ENTRY_COUNT += 1
        # process tree separately
        tree = entries[-1]
        tree_str = tree.get("tree", "")
        pairs = sketchy_conversion(tree_str)
        for pair in pairs:
            row = TransportGroupsTree(
                id=TREE_PAIRS_COUNT,
                parent_id=LABEL_TO_DB_ID[pair[0]],
                child_id=LABEL_TO_DB_ID[pair[1]],
            )
            session.add(row)
            TREE_PAIRS_COUNT += 1
    logging.info(f"Added {ENTRY_COUNT - 1} library entries")

    grp_count = 0
    for grp_file in groups_dir.glob("*.py"):
        entries = parse_entry(grp_file)
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
            grp_count += 1
    logging.info(f"Added {grp_count} group entries")

    session.commit()
    logging.info("Database commit complete")

if __name__ == "__main__":
    main()
