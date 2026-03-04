from pathlib import Path

from rmgdb.transport.schema import (
    Groups,
    GroupsTree,
    CriticalPointGroupContribution,
    TransportLibraries,
    TransportData,
    SCHEMA_BASE,
)
from rmgdb.transport.views import transport_groups_view_sql, transport_libraries_view_sql, label_pairs_view_sql

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rmgdatabase.common.tree_str_to_pairs import sketchy_conversion

# Create engine and SESSION
engine = create_engine("sqlite:///transport.db", echo=False)
Session = sessionmaker(bind=engine)
SESSION = Session()
SCHEMA_BASE.metadata.create_all(engine)

LABEL_TO_DB_ID = {None: None}

# Mock Classes for exec() ingestion
def TransportDataSpoof(**kwargs):
    return kwargs

def CriticalPointGroupContributionSpoof(**kwargs):
    return kwargs

# Map the groups in...
def entry_group_spoof(*, index, label, group, transportGroup=None, shortDesc="", longDesc=""):
    global ENTRY_COUNT
    global CPGC_COUNT
    global SESSION
    global CURRENT_NAME
    
    row = Groups(
        id=ENTRY_COUNT,
        name=CURRENT_NAME,
        short_description=shortDesc,
        long_description=longDesc,
        label=label,
        group=group,
    )
    LABEL_TO_DB_ID[label] = ENTRY_COUNT
    SESSION.add(row)
    
    # Process transportGroup data if it's not None
    if transportGroup is not None:
        cpgc_row = CriticalPointGroupContribution(
            id=CPGC_COUNT,
            parent_id=ENTRY_COUNT,
            Tc=transportGroup.get("Tc"),
            Pc=transportGroup.get("Pc"),
            Vc=transportGroup.get("Vc"),
            Tb=transportGroup.get("Tb"),
            structureIndex=transportGroup.get("structureIndex"),
        )
        SESSION.add(cpgc_row)
        CPGC_COUNT += 1
        
    ENTRY_COUNT += 1

def tree_spoof(tree_str):
    global TREE_PAIRS_COUNT
    global SESSION
    pairs = sketchy_conversion(tree_str)
    for pair in pairs:
        row = GroupsTree(
            id=TREE_PAIRS_COUNT,
            parent_id=LABEL_TO_DB_ID.get(pair[0]),
            child_id=LABEL_TO_DB_ID.get(pair[1]),
        )
        SESSION.add(row)
        TREE_PAIRS_COUNT += 1

ENTRY_COUNT = 0
CPGC_COUNT = 0
TREE_PAIRS_COUNT = 0

group_dir = Path("./original/groups")
for group_file in group_dir.glob("*.py"):
    CURRENT_NAME = group_file.stem
    exec(
        group_file.read_text(),
        {
            "entry": entry_group_spoof,
            "CriticalPointGroupContribution": CriticalPointGroupContributionSpoof,
            "tree": tree_spoof,
        },
    )


# Map the libraries in...
def entry_library_spoof(*, index, label, molecule, transport, shortDesc="", longDesc=""):
    global LIB_ENTRY_COUNT
    global TRANSPORT_DATA_COUNT
    global SESSION
    global CURRENT_NAME
    
    row = TransportLibraries(
        id=LIB_ENTRY_COUNT,
        name=CURRENT_NAME,
        short_description=shortDesc,
        long_description=longDesc,
        label=label,
        adjacency_list=molecule,
    )
    SESSION.add(row)

    # Some variables like epsilon are stored as tuples (value, 'units')
    # Unpack them safely
    def unpack(tup):
        return (tup[0], tup[1]) if isinstance(tup, tuple) else (tup, None)

    eps_val, eps_unit = unpack(transport.get("epsilon"))
    sig_val, sig_unit = unpack(transport.get("sigma"))
    dm_val, dm_unit = unpack(transport.get("dipoleMoment"))
    pol_val, pol_unit = unpack(transport.get("polarizability"))

    td_row = TransportData(
        id=TRANSPORT_DATA_COUNT,
        parent_id=LIB_ENTRY_COUNT,
        shapeIndex=transport.get("shapeIndex"),
        epsilon=eps_val,
        epsilon_unit=eps_unit,
        sigma=sig_val,
        sigma_unit=sig_unit,
        dipoleMoment=dm_val,
        dipoleMoment_unit=dm_unit,
        polarizability=pol_val,
        polarizability_unit=pol_unit,
        rotrelaxcollnum=transport.get("rotrelaxcollnum"),
    )
    SESSION.add(td_row)
    
    TRANSPORT_DATA_COUNT += 1
    LIB_ENTRY_COUNT += 1

LIB_ENTRY_COUNT = 0
TRANSPORT_DATA_COUNT = 0

library_dir = Path("./original/libraries")
for library_file in library_dir.glob("*.py"):
    CURRENT_NAME = library_file.stem
    exec(
        library_file.read_text(),
        {
            "entry": entry_library_spoof,
            "TransportData": TransportDataSpoof,
        },
    )

try:
    SESSION.commit()
except ValueError as e:
    SESSION.rollback()
    print(f"Error: {e}")

# Apply views
SESSION.execute(transport_groups_view_sql)
SESSION.execute(transport_libraries_view_sql)
SESSION.execute(label_pairs_view_sql)

SESSION.commit()
SESSION.close()
