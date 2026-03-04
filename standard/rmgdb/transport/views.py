from sqlalchemy import select, text

from rmgdb.transport.schema import TransportLibraries, TransportData

# Plain SQL View for Groups
transport_groups_view_sql = text("""CREATE VIEW transport_groups_view AS SELECT 
groups_table.name, groups_table.short_description, groups_table.long_description, groups_table.label, groups_table."group",
critical_point_group_contribution_table.Tc, critical_point_group_contribution_table.Pc, 
critical_point_group_contribution_table.Vc, critical_point_group_contribution_table.Tb, 
critical_point_group_contribution_table.structureIndex FROM groups_table
LEFT JOIN critical_point_group_contribution_table on critical_point_group_contribution_table.parent_id == groups_table.id""")

# Reusable View for Group Hierarchies
label_pairs_view_sql = text("""CREATE VIEW label_pairs_view AS SELECT parent_lookup.label as parent_label, child_lookup.label as child_label FROM groups_tree_table
JOIN groups_table child_lookup on child_lookup.id == groups_tree_table.child_id
JOIN groups_table parent_lookup on parent_lookup.id == groups_tree_table.parent_id""")

# Python SQLAlchemy Construction for Libraries
transport_data_view = (
    select(
        TransportData.parent_id.label("parent_id"),
        TransportData.shapeIndex.label("shapeIndex"),
        TransportData.epsilon.label("epsilon"),
        TransportData.epsilon_unit.label("epsilon_unit"),
        TransportData.sigma.label("sigma"),
        TransportData.sigma_unit.label("sigma_unit"),
        TransportData.dipoleMoment.label("dipoleMoment"),
        TransportData.dipoleMoment_unit.label("dipoleMoment_unit"),
        TransportData.polarizability.label("polarizability"),
        TransportData.polarizability_unit.label("polarizability_unit"),
        TransportData.rotrelaxcollnum.label("rotrelaxcollnum"),
    )
    .select_from(TransportData)
).subquery("inner_t")

view_query = (
    select(
        TransportLibraries.id,
        TransportLibraries.name,
        TransportLibraries.short_description,
        TransportLibraries.long_description,
        TransportLibraries.label,
        TransportLibraries.adjacency_list,
        transport_data_view.c.shapeIndex,
        transport_data_view.c.epsilon,
        transport_data_view.c.epsilon_unit,
        transport_data_view.c.sigma,
        transport_data_view.c.sigma_unit,
        transport_data_view.c.dipoleMoment,
        transport_data_view.c.dipoleMoment_unit,
        transport_data_view.c.polarizability,
        transport_data_view.c.polarizability_unit,
        transport_data_view.c.rotrelaxcollnum,
    )
    .select_from(transport_data_view)
    .outerjoin(
        TransportLibraries,
        TransportLibraries.id == transport_data_view.c.parent_id,
    )
)

view_name = "transport_libraries_view"
transport_libraries_view_sql = text(f"CREATE VIEW {view_name} AS {view_query}")
