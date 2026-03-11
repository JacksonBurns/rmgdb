from sqlalchemy import text

label_pairs_view_sql = text("""CREATE VIEW label_pairs_view AS 
SELECT t.id, p.name as name, p.label as parent_label, c.label as child_label 
FROM groups_tree_table t
JOIN groups_table c on c.id = t.child_id
JOIN groups_table p on p.id = t.parent_id""")

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
SELECT g.id, g.name, g.label, g."group", g.short_description, g.long_description, 
       g.solute_pointer, s.S as solute_S, s.B as solute_B, s.E as solute_E, s.L as solute_L, s.A as solute_A, s.V as solute_V,
       c.S as count_S, c.B as count_B, c.E as count_E, c.L as count_L, c.A as count_A
FROM groups_table g
LEFT JOIN solute_data_table s ON s.group_parent_id = g.id
LEFT JOIN data_count_gav_table c ON c.group_parent_id = g.id
""")
