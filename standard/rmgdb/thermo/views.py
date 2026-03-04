from sqlalchemy import select, text

label_pairs_view_sql = text("""CREATE VIEW label_pairs_view AS SELECT parent_lookup.label as parent_label, child_lookup.label as child_label FROM groups_tree_table
JOIN groups_table child_lookup on child_lookup.id == groups_tree_table.child_id
JOIN groups_table parent_lookup on parent_lookup.id == groups_tree_table.parent_id""")

thermo_groups_view_sql = text("""CREATE VIEW thermo_groups_view AS SELECT * FROM groups_table""")
thermo_libraries_view_sql = text("""CREATE VIEW thermo_libraries_view AS SELECT * FROM thermo_libraries_table""")
thermo_depositories_view_sql = text("""CREATE VIEW thermo_depositories_view AS SELECT * FROM thermo_depositories_table""")
