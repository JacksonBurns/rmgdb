from sqlalchemy import select, text

from rmgdb.solvation.schema import (
    SoluteData, SolventData, DataCountSolvent, DataCountGAV,
    SoluteLibrary, SolventLibrary, SolvationLibraries,
    Groups
)

# Create view for solvation groups with solute data
solvation_groups_view_sql = text("""CREATE VIEW solvation_groups_view AS 
SELECT 
    groups_table.name, 
    groups_table.short_description, 
    groups_table.long_description, 
    groups_table.label, 
    groups_table."group",
    solute_data_table.S,
    solute_data_table.B,
    solute_data_table.E,
    solute_data_table.L,
    solute_data_table.A,
    solute_data_table.V,
    data_count_gav_table.S as S_count,
    data_count_gav_table.B as B_count,
    data_count_gav_table.E as E_count,
    data_count_gav_table.L as L_count,
    data_count_gav_table.A as A_count
FROM groups_table
LEFT JOIN solute_data_table ON solute_data_table.parent_id = groups_table.id
LEFT JOIN data_count_gav_table ON data_count_gav_table.parent_id = groups_table.id""")

# Create view for label pairs (parent-child relationships)
label_pairs_view_sql = text("""CREATE VIEW label_pairs_view AS 
SELECT 
    parent_lookup.label AS parent_label, 
    child_lookup.label AS child_label 
FROM groups_tree_table
JOIN groups_table child_lookup ON child_lookup.id = groups_tree_table.child_id
JOIN groups_table parent_lookup ON parent_lookup.id = groups_tree_table.parent_id""")

# Create view for solute libraries with solute data
solute_view = (
    select(
        SoluteData.parent_id.label("parent_id"),
        SoluteData.S.label("S"),
        SoluteData.B.label("B"),
        SoluteData.E.label("E"),
        SoluteData.L.label("L"),
        SoluteData.A.label("A"),
        SoluteData.V.label("V"),
    )
    .select_from(SoluteData)
).subquery("solute_t")

# Create view for solvent libraries with solvent data
solvent_view = (
    select(
        SolventData.parent_id.label("parent_id"),
        # Abraham parameters for dGsolv
        SolventData.s_g.label("s_g"),
        SolventData.b_g.label("b_g"),
        SolventData.e_g.label("e_g"),
        SolventData.l_g.label("l_g"),
        SolventData.a_g.label("a_g"),
        SolventData.c_g.label("c_g"),
        # Mintz parameters for dHsolv
        SolventData.s_h.label("s_h"),
        SolventData.b_h.label("b_h"),
        SolventData.e_h.label("e_h"),
        SolventData.l_h.label("l_h"),
        SolventData.a_h.label("a_h"),
        SolventData.c_h.label("c_h"),
        # Viscosity parameters
        SolventData.A.label("A"),
        SolventData.B.label("B"),
        SolventData.C.label("C"),
        SolventData.D.label("D"),
        SolventData.E.label("E"),
        # Additional properties
        SolventData.alpha.label("alpha"),
        SolventData.beta.label("beta"),
        SolventData.eps.label("eps"),
        SolventData.name_in_coolprop.label("name_in_coolprop"),
    )
    .select_from(SolventData)
).subquery("solvent_t")

# Create view for data count information
data_count_view = (
    select(
        DataCountSolvent.parent_id.label("parent_id"),
        DataCountSolvent.dGsolvCount.label("dGsolvCount"),
        DataCountSolvent.dGsolvMAE_value.label("dGsolvMAE_value"),
        DataCountSolvent.dGsolvMAE_unit.label("dGsolvMAE_unit"),
        DataCountSolvent.dHsolvCount.label("dHsolvCount"),
        DataCountSolvent.dHsolvMAE_value.label("dHsolvMAE_value"),
        DataCountSolvent.dHsolvMAE_unit.label("dHsolvMAE_unit"),
    )
    .select_from(DataCountSolvent)
).subquery("data_count_t")

# Create comprehensive view for solute libraries
solute_library_view_query = (
    select(
        SoluteLibrary.id,
        SoluteLibrary.name,
        SoluteLibrary.short_description,
        SoluteLibrary.long_description,
        SoluteLibrary.label,
        SoluteLibrary.adjacency_list,
        solute_view.c.S,
        solute_view.c.B,
        solute_view.c.E,
        solute_view.c.L,
        solute_view.c.A,
        solute_view.c.V,
    )
    .select_from(solute_view)
    .outerjoin(
        SoluteLibrary,
        SoluteLibrary.id == solute_view.c.parent_id,
    )
)

# Create comprehensive view for solvent libraries
solvent_library_view_query = (
    select(
        SolventLibrary.id,
        SolventLibrary.name,
        SolventLibrary.short_description,
        SolventLibrary.long_description,
        SolventLibrary.label,
        SolventLibrary.adjacency_list,
        solvent_view.c.s_g,
        solvent_view.c.b_g,
        solvent_view.c.e_g,
        solvent_view.c.l_g,
        solvent_view.c.a_g,
        solvent_view.c.c_g,
        solvent_view.c.s_h,
        solvent_view.c.b_h,
        solvent_view.c.e_h,
        solvent_view.c.l_h,
        solvent_view.c.a_h,
        solvent_view.c.c_h,
        solvent_view.c.A,
        solvent_view.c.B,
        solvent_view.c.C,
        solvent_view.c.D,
        solvent_view.c.E,
        solvent_view.c.alpha,
        solvent_view.c.beta,
        solvent_view.c.eps,
        solvent_view.c.name_in_coolprop,
        data_count_view.c.dGsolvCount,
        data_count_view.c.dGsolvMAE_value,
        data_count_view.c.dGsolvMAE_unit,
        data_count_view.c.dHsolvCount,
        data_count_view.c.dHsolvMAE_value,
        data_count_view.c.dHsolvMAE_unit,
    )
    .select_from(solvent_view)
    .outerjoin(
        SolventLibrary,
        SolventLibrary.id == solvent_view.c.parent_id,
    )
    .outerjoin(
        data_count_view,
        data_count_view.c.parent_id == solvent_view.c.parent_id,
    )
)

# Create the views in the database
solute_library_view_name = "solute_libraries_view"
solute_libraries_view_sql = text(f"CREATE VIEW {solute_library_view_name} AS {solute_library_view_query}")

solvent_library_view_name = "solvent_libraries_view"
solvent_libraries_view_sql = text(f"CREATE VIEW {solvent_library_view_name} AS {solvent_library_view_query}")

# Create a combined view for all solvation libraries
solvation_libraries_view_query = (
    select(
        SolvationLibraries.id,
        SolvationLibraries.name,
        SolvationLibraries.short_description,
        SolvationLibraries.long_description,
        SolvationLibraries.label,
        SolvationLibraries.adjacency_list,
    )
    .select_from(SolvationLibraries)
)

solvation_libraries_view_name = "solvation_libraries_view"
solvation_libraries_view_sql = text(f"CREATE VIEW {solvation_libraries_view_name} AS {solvation_libraries_view_query}")
