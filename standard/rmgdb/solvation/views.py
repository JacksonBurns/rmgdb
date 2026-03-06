from sqlalchemy import text

label_pairs_view_sql = text("""CREATE VIEW label_pairs_view AS 
SELECT parent_lookup.label as parent_label, child_lookup.label as child_label 
FROM groups_tree_table
JOIN groups_table child_lookup on child_lookup.id == groups_tree_table.child_id
JOIN groups_table parent_lookup on parent_lookup.id == groups_tree_table.parent_id""")

solute_libraries_view_sql = text("""CREATE VIEW solute_libraries_view AS 
SELECT 
    l.id, l.name, l.short_description, l.long_description, l.label, l.molecule,
    sd.S, sd.B, sd.E, sd.L, sd.A, sd.V
FROM solute_libraries_table l
LEFT JOIN solute_data_table sd ON sd.solute_library_parent_id = l.id
""")

solvent_libraries_view_sql = text("""CREATE VIEW solvent_libraries_view AS 
SELECT 
    l.id, l.name, l.short_description, l.long_description, l.label, l.molecule,
    sd.s_g, sd.b_g, sd.e_g, sd.l_g, sd.a_g, sd.c_g,
    sd.s_h, sd.b_h, sd.e_h, sd.l_h, sd.a_h, sd.c_h,
    sd.A, sd.B, sd.C, sd.D, sd.E,
    sd.alpha, sd.beta, sd.eps, sd.n, sd.name_in_coolprop,
    dcs.dGsolvCount, dcs.dGsolvMAE_val, dcs.dGsolvMAE_unit,
    dcs.dHsolvCount, dcs.dHsolvMAE_val, dcs.dHsolvMAE_unit
FROM solvent_libraries_table l
LEFT JOIN solvent_data_table sd ON sd.solvent_library_parent_id = l.id
LEFT JOIN data_count_solvent_table dcs ON dcs.solvent_library_parent_id = l.id
""")

solute_groups_view_sql = text("""CREATE VIEW solute_groups_view AS 
SELECT 
    g.id, g.name, g.short_description, g.long_description, g.label, g."group", g.solute_pointer,
    sd.S as solute_S, sd.B as solute_B, sd.E as solute_E, sd.L as solute_L, sd.A as solute_A, sd.V as solute_V,
    dc.S as count_S, dc.B as count_B, dc.E as count_E, dc.L as count_L, dc.A as count_A
FROM groups_table g
LEFT JOIN solute_data_table sd ON sd.group_parent_id = g.id
LEFT JOIN data_count_gav_table dc ON dc.group_parent_id = g.id
""")
