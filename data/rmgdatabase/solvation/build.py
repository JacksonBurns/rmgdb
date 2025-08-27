from pathlib import Path

from rmgdb.solvation.schema import (
    # Group
    Groups,
    GroupsTree,
    SoluteData,
    # Library
    SolvationLibraries,
    SoluteLibrary,
    SolventLibrary,
    SolventData,
    DataCountGAV,
    DataCountSolvent,
    # declarative SCHEMA_BASE,
    SCHEMA_BASE,
)
from rmgdb.solvation.views import solvation_groups_view_sql, solute_libraries_view_sql, solvent_libraries_view_sql, label_pairs_view_sql

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
    """Mock SoluteData class for use in exec context"""
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
    
    # Add solute data if present
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

def DataCountGAVSpoof(*, S, B, E, L, A):
    global DATA_COUNT_GAV_COUNT
    global ENTRY_COUNT
    global SESSION
    new_data_count = DataCountGAV(
        id=DATA_COUNT_GAV_COUNT,
        parent_id=ENTRY_COUNT,
        S=S,
        B=B,
        E=E,
        L=L,
        A=A,
    )
    DATA_COUNT_GAV_COUNT += 1
    SESSION.add(new_data_count)

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
            "SoluteData": SoluteDataSpoof,
            "DataCountGAV": DataCountGAVSpoof,
        },
    )

# now map the libraries in


def SolventDataSpoof(*, s_g, b_g, e_g, l_g, a_g, c_g, s_h, b_h, e_h, l_h, a_h, c_h, 
                     A, B, C, D, E, alpha, beta, eps, name_in_coolprop):
    global SOLVENT_DATA_COUNT
    global ENTRY_COUNT
    global SESSION
    new_solvent = SolventData(
        id=SOLVENT_DATA_COUNT,
        parent_id=ENTRY_COUNT,
        s_g=s_g,
        b_g=b_g,
        e_g=e_g,
        l_g=l_g,
        a_g=a_g,
        c_g=c_g,
        s_h=s_h,
        b_h=b_h,
        e_h=e_h,
        l_h=l_h,
        a_h=a_h,
        c_h=c_h,
        A=A,
        B=B,
        C=C,
        D=D,
        E=E,
        alpha=alpha,
        beta=beta,
        eps=eps,
        name_in_coolprop=name_in_coolprop,
    )
    SOLVENT_DATA_COUNT += 1
    SESSION.add(new_solvent)


def DataCountSolventSpoof(*, dGsolvCount, dGsolvMAE, dHsolvCount, dHsolvMAE):
    global DATA_COUNT_COUNT
    global ENTRY_COUNT
    global SESSION
    new_data_count = DataCountSolvent(
        id=DATA_COUNT_COUNT,
        parent_id=ENTRY_COUNT,
        dGsolvCount=dGsolvCount,
        dGsolvMAE_value=dGsolvMAE[0] if dGsolvMAE is not None else None,
        dGsolvMAE_unit=dGsolvMAE[1] if dGsolvMAE is not None else None,
        dHsolvCount=dHsolvCount,
        dHsolvMAE_value=dHsolvMAE[0] if dHsolvMAE is not None else None,
        dHsolvMAE_unit=dHsolvMAE[1] if dHsolvMAE is not None else None,
    )
    DATA_COUNT_COUNT += 1
    SESSION.add(new_data_count)


def entry_spoof_library(*, index, label, molecule, solute=None, solvent=None, shortDesc, longDesc, dataCount=None):
    global ENTRY_COUNT
    global SESSION
    global CURRENT_NAME
    
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
            adjacency_list=molecule,
        )
    elif solvent is not None:
        row = SolventLibrary(
            id=ENTRY_COUNT,
            name=CURRENT_NAME,
            short_description=shortDesc,
            long_description=longDesc,
            label=label,
            adjacency_list=molecule,
        )
    else:
        # Fallback to generic solvation library
        row = SolvationLibraries(
            id=ENTRY_COUNT,
            name=CURRENT_NAME,
            short_description=shortDesc,
            long_description=longDesc,
            label=label,
            adjacency_list=molecule,
        )
    
    ENTRY_COUNT += 1
    SESSION.add(row)


# global variable abuse
SOLUTE_DATA_COUNT = 0
SOLVENT_DATA_COUNT = 0
DATA_COUNT_COUNT = 0
ENTRY_COUNT = 0

library_dir = Path("./original/libraries")
for library_file in library_dir.glob("*"):
    CURRENT_NAME = library_file.stem
    exec(
        library_file.read_text(),
        {
            "entry": entry_spoof_library,
            "SoluteData": SoluteDataSpoof,
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
SESSION.execute(solvation_groups_view_sql)
SESSION.execute(solute_libraries_view_sql)
SESSION.execute(solvent_libraries_view_sql)
SESSION.execute(label_pairs_view_sql)

SESSION.close()
