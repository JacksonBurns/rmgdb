from sqlalchemy import text

label_pairs_view_sql = text("""CREATE VIEW label_pairs_view AS 
SELECT p.label as parent_label, c.label as child_label 
FROM kinetics_family_groups_tree_table t
JOIN kinetics_family_groups_table c on c.id = t.child_id
JOIN kinetics_family_groups_table p on p.id = t.parent_id""")

kinetics_library_reaction_species_view_sql = text("""CREATE VIEW kinetics_library_reaction_species_view AS
SELECT rs.library_reaction_id, r.label as reaction_label, rs.species_label, rs.role, d.adjacency_list
FROM kinetics_library_reaction_species_table rs
JOIN kinetics_library_reactions_table r ON r.id = rs.library_reaction_id
LEFT JOIN kinetics_library_dictionary_table d ON d.library_id = r.library_id AND d.label = rs.species_label
""")

kinetics_family_training_reaction_species_view_sql = text("""CREATE VIEW kinetics_family_training_reaction_species_view AS
SELECT rs.training_reaction_id, r.label as reaction_label, rs.species_label, rs.role, d.adjacency_list
FROM kinetics_family_training_reaction_species_table rs
JOIN kinetics_family_training_reactions_table r ON r.id = rs.training_reaction_id
LEFT JOIN kinetics_family_training_dictionary_table d ON d.family_id = r.family_id AND d.label = rs.species_label
""")

all_library_kinetics_view_sql = text("""CREATE VIEW all_library_kinetics_view AS 
SELECT 
    l.name as library_name, r.id as reaction_id, r.label, r.degeneracy, r.short_description, r.long_description, r.rank,
    a.kinetics_type as arrhenius_type, a.A_val, a.A_unit, a.n, a.Ea_val, a.Ea_unit, a.T0_val, a.T0_unit,
    ep.kinetics_type as arrhenius_ep_type, ep.alpha as ep_alpha, ep.E0_val as ep_E0_val, ep.E0_unit as ep_E0_unit,
    t.alpha as troe_alpha, t.high_A_val as troe_high_A, t.low_A_val as troe_low_A, t.T3_val as troe_T3,
    c.Tmin_val as cheb_Tmin, c.Pmin_val as cheb_Pmin, c.degreeT, c.degreeP,
    pd.id as pdep_id,
    ts.id as solute_ts_id
FROM kinetics_library_reactions_table r
JOIN kinetics_libraries_table l ON l.id = r.library_id
LEFT JOIN kinetics_arrhenius_table a ON a.library_reaction_id = r.id
LEFT JOIN kinetics_arrhenius_ep_table ep ON ep.library_reaction_id = r.id
LEFT JOIN kinetics_troe_table t ON t.library_reaction_id = r.id
LEFT JOIN kinetics_chebyshev_table c ON c.library_reaction_id = r.id
LEFT JOIN kinetics_pdep_arrhenius_table pd ON pd.library_reaction_id = r.id
LEFT JOIN kinetics_solute_ts_diff_table ts ON ts.library_reaction_id = r.id
""")

all_family_rules_kinetics_view_sql = text("""CREATE VIEW all_family_rules_kinetics_view AS 
SELECT 
    f.name as family_name, r.id as rule_id, r.label, r.short_description, r.long_description, r.rank,
    a.kinetics_type as arrhenius_type, a.A_val, a.A_unit, a.n, a.Ea_val, a.Ea_unit, a.T0_val, a.T0_unit,
    ep.kinetics_type as arrhenius_ep_type, ep.alpha as ep_alpha, ep.E0_val as ep_E0_val, ep.E0_unit as ep_E0_unit,
    t.alpha as troe_alpha, t.high_A_val as troe_high_A, t.low_A_val as troe_low_A, t.T3_val as troe_T3,
    c.Tmin_val as cheb_Tmin, c.Pmin_val as cheb_Pmin, c.degreeT, c.degreeP,
    pd.id as pdep_id,
    ts.id as solute_ts_id
FROM kinetics_family_rules_table r
JOIN kinetics_families_table f ON f.id = r.family_id
LEFT JOIN kinetics_arrhenius_table a ON a.family_rule_id = r.id
LEFT JOIN kinetics_arrhenius_ep_table ep ON ep.family_rule_id = r.id
LEFT JOIN kinetics_troe_table t ON t.family_rule_id = r.id
LEFT JOIN kinetics_chebyshev_table c ON c.family_rule_id = r.id
LEFT JOIN kinetics_pdep_arrhenius_table pd ON pd.family_rule_id = r.id
LEFT JOIN kinetics_solute_ts_diff_table ts ON ts.family_rule_id = r.id
""")

kinetics_library_dictionary_view_sql = text("""CREATE VIEW kinetics_library_dictionary_view AS
SELECT l.name as library_name, d.label, d.adjacency_list
FROM kinetics_library_dictionary_table d
JOIN kinetics_libraries_table l ON l.id = d.library_id
""")

kinetics_family_groups_view_sql = text("""CREATE VIEW kinetics_family_groups_view AS
SELECT f.name as family_name, g.label, g.group_adj_list, g.short_description, g.long_description
FROM kinetics_family_groups_table g
JOIN kinetics_families_table f ON f.id = g.family_id
""")

kinetics_family_forbidden_groups_view_sql = text("""CREATE VIEW kinetics_family_forbidden_groups_view AS
SELECT f.name as family_name, g.label, g.group_adj_list, g.short_description, g.long_description
FROM kinetics_family_forbidden_groups_table g
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
