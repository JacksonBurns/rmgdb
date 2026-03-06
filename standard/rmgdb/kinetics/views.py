from sqlalchemy import text

label_pairs_view_sql = text("""CREATE VIEW label_pairs_view AS 
SELECT p.label as parent_label, c.label as child_label 
FROM kinetics_family_groups_tree_table t
JOIN kinetics_family_groups_table c on c.id = t.child_id
JOIN kinetics_family_groups_table p on p.id = t.parent_id""")

kinetics_library_reactions_view_sql = text("""CREATE VIEW kinetics_library_reactions_view AS 
SELECT 
    l.name as library_name, r.label, r.degeneracy, r.short_description, r.long_description, r.rank,
    kd.type, kd.A_val, kd.A_unit, kd.n, kd.Ea_val, kd.Ea_unit, kd.T0_val, kd.T0_unit,
    kd.w0_val, kd.w0_unit, kd.E0_val, kd.E0_unit, kd.Tmin_val, kd.Tmin_unit, kd.Tmax_val, kd.Tmax_unit, kd.comment
FROM kinetics_library_reactions_table r
JOIN kinetics_libraries_table l ON l.id = r.library_id
LEFT JOIN kinetics_data_table kd ON kd.library_reaction_id = r.id
""")

kinetics_family_rules_view_sql = text("""CREATE VIEW kinetics_family_rules_view AS 
SELECT 
    f.name as family_name, r.label, r.short_description, r.long_description, r.rank,
    kd.type, kd.A_val, kd.A_unit, kd.n, kd.Ea_val, kd.Ea_unit, kd.T0_val, kd.T0_unit,
    kd.w0_val, kd.w0_unit, kd.E0_val, kd.E0_unit, kd.Tmin_val, kd.Tmin_unit, kd.Tmax_val, kd.Tmax_unit, kd.comment
FROM kinetics_family_rules_table r
JOIN kinetics_families_table f ON f.id = r.family_id
LEFT JOIN kinetics_data_table kd ON kd.family_rule_id = r.id
""")

kinetics_family_training_reactions_view_sql = text("""CREATE VIEW kinetics_family_training_reactions_view AS 
SELECT 
    f.name as family_name, r.label, r.degeneracy, r.short_description, r.long_description, r.rank,
    kd.type, kd.A_val, kd.A_unit, kd.n, kd.Ea_val, kd.Ea_unit, kd.T0_val, kd.T0_unit,
    kd.w0_val, kd.w0_unit, kd.E0_val, kd.E0_unit, kd.Tmin_val, kd.Tmin_unit, kd.Tmax_val, kd.Tmax_unit, kd.comment
FROM kinetics_family_training_reactions_table r
JOIN kinetics_families_table f ON f.id = r.family_id
LEFT JOIN kinetics_data_table kd ON kd.family_training_reaction_id = r.id
""")

kinetics_library_dictionary_view_sql = text("""CREATE VIEW kinetics_library_dictionary_view AS
SELECT l.name as library_name, d.label, d.adjacency_list
FROM kinetics_library_dictionary_table d
JOIN kinetics_libraries_table l ON l.id = d.library_id
""")

kinetics_family_groups_view_sql = text("""CREATE VIEW kinetics_family_groups_view AS
SELECT f.name as family_name, g.label, g.group_adj_list
FROM kinetics_family_groups_table g
JOIN kinetics_families_table f ON f.id = g.family_id
""")

kinetics_family_training_dictionary_view_sql = text("""CREATE VIEW kinetics_family_training_dictionary_view AS
SELECT f.name as family_name, d.label, d.adjacency_list
FROM kinetics_family_training_dictionary_table d
JOIN kinetics_families_table f ON f.id = d.family_id
""")

kinetics_families_view_sql = text("""CREATE VIEW kinetics_families_view AS
SELECT f.name, f.short_description, f.long_description, f.template, f.recipe, f.reversible, f.reverse_map, f.reactant_num, f.product_num, f.auto_generated
FROM kinetics_families_table f
""")