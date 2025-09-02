from pathlib import Path

from rmgdb.solvation.schema import (
    # Group
    Groups,
    GroupsTree,
    SoluteData,
    DataCountGAV,
    # Library
    SolvationLibraries,
    SoluteLibrary,
    SoluteLibraryData,
    SolventLibrary,
    SolventData,
    DataCountSolvent,
    # declarative SCHEMA_BASE,
    SCHEMA_BASE,
)
from rmgdb.solvation.views import solute_groups_view_sql, solute_libraries_view_sql, solvent_libraries_view_sql, label_pairs_view_sql

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rmgdatabase.common.tree_str_to_pairs import sketchy_conversion


# Create engine and SESSION
engine = create_engine("sqlite:///solvation.db", echo=False)
Session = sessionmaker(bind=engine)
SESSION = Session()
SCHEMA_BASE.metadata.create_all(engine)

LABEL_TO_DB_ID = {None: None}  # None: None for root/leaf nodes


# map the groups in...
def SoluteDataSpoof(*, S, B, E, L, A, V = None):
    """Mock SoluteData class for use in exec context - for GROUPS only"""
    class MockSoluteData:
        def __init__(self, S, B, E, L, A, V = None):
            self.S = S
            self.B = B
            self.E = E
            self.L = L
            self.A = A
            self.V = V
    return MockSoluteData(S, B, E, L, A, V)


def DataCountGAVSpoof(*, S, B, E, L, A):
    """Mock DataCountGAV class for use in exec context"""
    class MockDataCountGAV:
        def __init__(self, S, B, E, L, A):
            self.S = S
            self.B = B
            self.E = E
            self.L = L
            self.A = A
    return MockDataCountGAV(S, B, E, L, A)


def entry_spoof(*, index, label, group, solute, shortDesc, longDesc, dataCount=None):
    global ENTRY_COUNT
    global SESSION
    global CURRENT_NAME
    global GROUP_SOLUTE_COUNT
    global DATA_COUNT_GAV_COUNT

    row = Groups(
        id=ENTRY_COUNT,
        name=CURRENT_NAME,
        short_description=shortDesc,
        long_description=longDesc,
        label=label,
        group=group,
    )
    LABEL_TO_DB_ID[label] = ENTRY_COUNT
    ENTRY_COUNT += 1
    SESSION.add(row)
    
    # Add solute data if present (this is GROUP solute data, not library data)
    if solute is not None:
        solute_row = SoluteData(
            id=GROUP_SOLUTE_COUNT,
            parent_id=ENTRY_COUNT - 1,  # Use the group we just added
            S=solute.S if hasattr(solute, 'S') else None,
            B=solute.B if hasattr(solute, 'B') else None,
            E=solute.E if hasattr(solute, 'E') else None,
            L=solute.L if hasattr(solute, 'L') else None,
            A=solute.A if hasattr(solute, 'A') else None,
            V=solute.V if hasattr(solute, 'V') else None,
        )
        SESSION.add(solute_row)
        
        GROUP_SOLUTE_COUNT += 1
    
    # Add data count if present
    if dataCount is not None:
        data_count_row = DataCountGAV(
            id=DATA_COUNT_GAV_COUNT,
            parent_id=ENTRY_COUNT - 1,  # Use the group we just added
            S=dataCount.S if hasattr(dataCount, 'S') else None,
            B=dataCount.B if hasattr(dataCount, 'B') else None,
            E=dataCount.E if hasattr(dataCount, 'E') else None,
            L=dataCount.L if hasattr(dataCount, 'L') else None,
            A=dataCount.A if hasattr(dataCount, 'A') else None,
        )
        SESSION.add(data_count_row)
        
        DATA_COUNT_GAV_COUNT += 1


def tree_spoof(tree_str):
    global TREE_PAIRS_COUNT
    global SESSION
    pairs = sketchy_conversion(tree_str)
    for pair in pairs:
        row = GroupsTree(
            id=TREE_PAIRS_COUNT,
            parent_id=LABEL_TO_DB_ID[pair[0]],
            child_id=LABEL_TO_DB_ID[pair[1]],
        )
        SESSION.add(row)
        TREE_PAIRS_COUNT += 1

# Load groups first
ENTRY_COUNT = 0
GROUP_SOLUTE_COUNT = 0
TREE_PAIRS_COUNT = 0
DATA_COUNT_GAV_COUNT = 0
group_dir = Path("./original/groups")
for group_file in group_dir.glob("*"):
    CURRENT_NAME = group_file.stem
    exec(
        group_file.read_text(),
        {  # we could just give our functions the exact same name as the file, but we do this for clarity/explicitness
            "entry": entry_spoof,
            "tree": tree_spoof,
            "SoluteData": SoluteDataSpoof,  # This is for GROUPS only
            "DataCountGAV": DataCountGAVSpoof,
        },
    )

# now map the libraries in - SEPARATE from groups

def SoluteLibraryDataSpoof(*, S, B, E, L, A, V = None):
    """Mock SoluteLibraryData class for use in exec context - for LIBRARIES only"""
    class MockSoluteLibraryData:
        def __init__(self, S, B, E, L, A, V = None):
            self.S = S
            self.B = B
            self.E = E
            self.L = L
            self.A = A
            self.V = V
    return MockSoluteLibraryData(S, B, E, L, A, V)


def SolventDataSpoof(*, s_g, b_g, e_g, l_g, a_g, c_g, s_h, b_h, e_h, l_h, a_h, c_h, 
                     A, B, C, D, E, alpha, beta, eps, name_in_coolprop):
    """Return a plain dict with solvent fields for entry_spoof_library to insert."""
    return {
        "s_g": s_g,
        "b_g": b_g,
        "e_g": e_g,
        "l_g": l_g,
        "a_g": a_g,
        "c_g": c_g,
        "s_h": s_h,
        "b_h": b_h,
        "e_h": e_h,
        "l_h": l_h,
        "a_h": a_h,
        "c_h": c_h,
        "A": A,
        "B": B,
        "C": C,
        "D": D,
        "E": E,
        "alpha": alpha,
        "beta": beta,
        "eps": eps,
        "name_in_coolprop": name_in_coolprop,
    }


def DataCountSolventSpoof(*, dGsolvCount, dGsolvMAE, dHsolvCount, dHsolvMAE):
    """Return a plain dict for data count; entry_spoof_library will insert."""
    return {
        "dGsolvCount": dGsolvCount,
        "dGsolvMAE": dGsolvMAE,
        "dHsolvCount": dHsolvCount,
        "dHsolvMAE": dHsolvMAE,
    }


def entry_spoof_library(*, index, label, molecule, solute=None, solvent=None, shortDesc, longDesc, dataCount=None):
    global ENTRY_COUNT
    global SESSION
    global CURRENT_NAME
    global SOLUTE_LIBRARY_DATA_COUNT
    global SOLVENT_DATA_COUNT
    global DATA_COUNT_COUNT
    
    # Ensure molecule is a string
    if isinstance(molecule, list):
        # return all molecules as a string joined by a " + "
        # this is required becaues of some entries like 
        #     label = "methanol_50_water_50",
        #     molecule = ["CO", "O"],
        # TODO: handle better, maybe DB has 2+ molecules?
        molecule = " + ".join(molecule)
    else:
        molecule = str(molecule)
    
    # Determine if this is a solute or solvent library entry
    if solute is not None:
        row = SoluteLibrary(
            id=ENTRY_COUNT,
            name=CURRENT_NAME,
            short_description=shortDesc,
            long_description=longDesc,
            label=label,
            molecule=molecule,
        )
        SESSION.add(row)
        
        # Add solute library data (separate from group data)
        solute_dict = solute
        new_solute_library_data = SoluteLibraryData(
            id=SOLUTE_LIBRARY_DATA_COUNT,
            parent_id=ENTRY_COUNT,
            S=solute_dict.S if hasattr(solute_dict, 'S') else None,
            B=solute_dict.B if hasattr(solute_dict, 'B') else None,
            E=solute_dict.E if hasattr(solute_dict, 'E') else None,
            L=solute_dict.L if hasattr(solute_dict, 'L') else None,
            A=solute_dict.A if hasattr(solute_dict, 'A') else None,
            V=solute_dict.V if hasattr(solute_dict, 'V') else None,
        )
        SESSION.add(new_solute_library_data)
        SOLUTE_LIBRARY_DATA_COUNT += 1
        
    elif solvent is not None:
        row = SolventLibrary(
            id=ENTRY_COUNT,
            name=CURRENT_NAME,
            short_description=shortDesc,
            long_description=longDesc,
            label=label,
            molecule=molecule,
        )
        SESSION.add(row)
        
        # Add solvent data from plain dict
        solvent_dict = solvent
        new_solvent = SolventData(
            id=SOLVENT_DATA_COUNT,
            parent_id=ENTRY_COUNT,
            s_g=solvent_dict.get("s_g"),
            b_g=solvent_dict.get("b_g"),
            e_g=solvent_dict.get("e_g"),
            l_g=solvent_dict.get("l_g"),
            a_g=solvent_dict.get("a_g"),
            c_g=solvent_dict.get("c_g"),
            s_h=solvent_dict.get("s_h"),
            b_h=solvent_dict.get("b_h"),
            e_h=solvent_dict.get("e_h"),
            l_h=solvent_dict.get("l_h"),
            a_h=solvent_dict.get("a_h"),
            c_h=solvent_dict.get("c_h"),
            A=solvent_dict.get("A"),
            B=solvent_dict.get("B"),
            C=solvent_dict.get("C"),
            D=solvent_dict.get("D"),
            E=solvent_dict.get("E"),
            alpha=solvent_dict.get("alpha"),
            beta=solvent_dict.get("beta"),
            eps=solvent_dict.get("eps"),
            name_in_coolprop=solvent_dict.get("name_in_coolprop"),
        )
        SESSION.add(new_solvent)
        SOLVENT_DATA_COUNT += 1
        
        # Add data count if present (from separate dataCount arg)
        if dataCount is not None:
            new_data_count = DataCountSolvent(
                id=DATA_COUNT_COUNT,
                parent_id=ENTRY_COUNT,
                dGsolvCount=dataCount.get("dGsolvCount"),
                dGsolvMAE_value=(dataCount.get("dGsolvMAE") or [None, None])[0],
                dGsolvMAE_unit=(dataCount.get("dGsolvMAE") or [None, None])[1],
                dHsolvCount=dataCount.get("dHsolvCount"),
                dHsolvMAE_value=(dataCount.get("dHsolvMAE") or [None, None])[0],
                dHsolvMAE_unit=(dataCount.get("dHsolvMAE") or [None, None])[1],
            )
            SESSION.add(new_data_count)
            DATA_COUNT_COUNT += 1
    else:
        # Fallback to generic solvation library
        row = SolvationLibraries(
            id=ENTRY_COUNT,
            name=CURRENT_NAME,
            short_description=shortDesc,
            long_description=longDesc,
            label=label,
            molecule=molecule,
        )
        SESSION.add(row)
    
    ENTRY_COUNT += 1


# global variable abuse for libraries (separate from groups)
SOLUTE_LIBRARY_DATA_COUNT = 0
SOLVENT_DATA_COUNT = 0
DATA_COUNT_COUNT = 0
ENTRY_COUNT = 0  # Reset counter for libraries

library_dir = Path("./original/libraries")
for library_file in library_dir.glob("*"):
    CURRENT_NAME = library_file.stem
    exec(
        library_file.read_text(),
        {
            "entry": entry_spoof_library,
            "SoluteData": SoluteLibraryDataSpoof,  # This is for LIBRARIES only
            "SolventData": SolventDataSpoof,
            "DataCountSolvent": DataCountSolventSpoof,
        },
    )

try:
    SESSION.commit()
except ValueError as e:
    SESSION.rollback()
    print(f"Error: {e}")

# make the views we need
SESSION.execute(solute_groups_view_sql)
SESSION.execute(solute_libraries_view_sql)
SESSION.execute(solvent_libraries_view_sql)
SESSION.execute(label_pairs_view_sql)

SESSION.close()
