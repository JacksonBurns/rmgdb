from sqlalchemy import text

label_pairs_view_sql = text("""CREATE VIEW label_pairs_view AS 
SELECT t.id, p.label as parent_label, c.label as child_label 
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

# ------------------------------------------------------------------------
# Wide Flattened Unified Views (Re-Joins All Data Tables To Reactions)
# ------------------------------------------------------------------------

all_library_kinetics_view_sql = text("""CREATE VIEW all_library_kinetics_view AS 
WITH adj_reactions AS (
    SELECT library_reaction_id,
           GROUP_CONCAT(CASE WHEN role = 'reactant' THEN adjacency_list END, '\n + \n') || 
           '\n <=> \n' ||
           GROUP_CONCAT(CASE WHEN role = 'product' THEN adjacency_list END, '\n + \n') as adjacency_reaction
    FROM kinetics_library_reaction_species_view
    GROUP BY library_reaction_id
)
SELECT 
    l.name as library_name, r.id as reaction_id, r.label, ar.adjacency_reaction, r.degeneracy, r.short_description, r.long_description, r.rank,
    
    COALESCE(
        a.kinetics_type, 
        ep.kinetics_type, 
        bm.kinetics_type,
        CASE WHEN m.id IS NOT NULL THEN 'Marcus' END,
        CASE WHEN t.id IS NOT NULL THEN 'Troe' END,
        CASE WHEN lind.id IS NOT NULL THEN 'Lindemann' END,
        CASE WHEN tb.id IS NOT NULL THEN 'ThirdBody' END,
        CASE WHEN c.id IS NOT NULL THEN 'Chebyshev' END,
        CASE WHEN pd.id IS NOT NULL THEN 'PDepArrhenius' END,
        CASE WHEN ts.id IS NOT NULL THEN 'SoluteTSDiffData' END
    ) AS overall_kinetics_type,

    a.A_val as arr_A_val, a.A_unit as arr_A_unit, a.n as arr_n, a.Ea_val as arr_Ea_val, a.Ea_unit as arr_Ea_unit, a.T0_val as arr_T0_val, a.T0_unit as arr_T0_unit,
    ep.alpha as ep_alpha, ep.E0_val as ep_E0_val, ep.E0_unit as ep_E0_unit,
    bm.w0_val as bm_w0_val, bm.w0_unit as bm_w0_unit, bm.E0_val as bm_E0_val, bm.E0_unit as bm_E0_unit,
    m.A_val as marcus_A_val, m.A_unit as marcus_A_unit, m.n as marcus_n, m.beta_val as marcus_beta_val, m.beta_unit as marcus_beta_unit, m.wr_val as marcus_wr_val, m.wr_unit as marcus_wr_unit, m.wp_val as marcus_wp_val, m.wp_unit as marcus_wp_unit, m.lmbd_o_val as marcus_lmbd_o_val, m.lmbd_o_unit as marcus_lmbd_o_unit,
    
    t.alpha as troe_alpha, t.T3_val as troe_T3, t.T1_val as troe_T1, t.T2_val as troe_T2, 
    t.high_A_val as troe_high_A, t.high_n as troe_high_n, t.high_Ea_val as troe_high_Ea,
    t.low_A_val as troe_low_A, t.low_n as troe_low_n, t.low_Ea_val as troe_low_Ea,
    
    lind.high_A_val as lind_high_A, lind.high_n as lind_high_n, lind.high_Ea_val as lind_high_Ea,
    lind.low_A_val as lind_low_A, lind.low_n as lind_low_n, lind.low_Ea_val as lind_low_Ea,
    tb.low_A_val as tb_low_A, tb.low_n as tb_low_n, tb.low_Ea_val as tb_low_Ea,
    c.Tmin_val as cheb_Tmin, c.Pmin_val as cheb_Pmin, c.degreeT as cheb_degreeT, c.degreeP as cheb_degreeP,
    pd.id as pdep_id,
    ts.id as solute_ts_id
FROM kinetics_library_reactions_table r
JOIN kinetics_libraries_table l ON l.id = r.library_id
LEFT JOIN adj_reactions ar ON ar.library_reaction_id = r.id
LEFT JOIN kinetics_arrhenius_table a ON a.library_reaction_id = r.id
LEFT JOIN kinetics_arrhenius_ep_table ep ON ep.library_reaction_id = r.id
LEFT JOIN kinetics_arrhenius_bm_table bm ON bm.library_reaction_id = r.id
LEFT JOIN kinetics_marcus_table m ON m.library_reaction_id = r.id
LEFT JOIN kinetics_troe_table t ON t.library_reaction_id = r.id
LEFT JOIN kinetics_lindemann_table lind ON lind.library_reaction_id = r.id
LEFT JOIN kinetics_third_body_table tb ON tb.library_reaction_id = r.id
LEFT JOIN kinetics_chebyshev_table c ON c.library_reaction_id = r.id
LEFT JOIN kinetics_pdep_arrhenius_table pd ON pd.library_reaction_id = r.id
LEFT JOIN kinetics_solute_ts_diff_table ts ON ts.library_reaction_id = r.id
""")

all_family_training_kinetics_view_sql = text("""CREATE VIEW all_family_training_kinetics_view AS 
WITH adj_reactions AS (
    SELECT training_reaction_id,
           GROUP_CONCAT(CASE WHEN role = 'reactant' THEN adjacency_list END, '\n + \n') || 
           '\n <=> \n' ||
           GROUP_CONCAT(CASE WHEN role = 'product' THEN adjacency_list END, '\n + \n') as adjacency_reaction
    FROM kinetics_family_training_reaction_species_view
    GROUP BY training_reaction_id
)
SELECT 
    f.name as family_name, r.id as reaction_id, r.label, ar.adjacency_reaction, r.degeneracy, r.short_description, r.long_description, r.rank,
    
    COALESCE(
        a.kinetics_type, 
        ep.kinetics_type, 
        bm.kinetics_type,
        CASE WHEN m.id IS NOT NULL THEN 'Marcus' END,
        CASE WHEN t.id IS NOT NULL THEN 'Troe' END,
        CASE WHEN lind.id IS NOT NULL THEN 'Lindemann' END,
        CASE WHEN tb.id IS NOT NULL THEN 'ThirdBody' END,
        CASE WHEN c.id IS NOT NULL THEN 'Chebyshev' END,
        CASE WHEN pd.id IS NOT NULL THEN 'PDepArrhenius' END,
        CASE WHEN ts.id IS NOT NULL THEN 'SoluteTSDiffData' END
    ) AS overall_kinetics_type,

    a.A_val as arr_A_val, a.A_unit as arr_A_unit, a.n as arr_n, a.Ea_val as arr_Ea_val, a.Ea_unit as arr_Ea_unit, a.T0_val as arr_T0_val, a.T0_unit as arr_T0_unit,
    ep.alpha as ep_alpha, ep.E0_val as ep_E0_val, ep.E0_unit as ep_E0_unit,
    bm.w0_val as bm_w0_val, bm.w0_unit as bm_w0_unit, bm.E0_val as bm_E0_val, bm.E0_unit as bm_E0_unit,
    m.A_val as marcus_A_val, m.A_unit as marcus_A_unit, m.n as marcus_n, m.beta_val as marcus_beta_val, m.beta_unit as marcus_beta_unit, m.wr_val as marcus_wr_val, m.wr_unit as marcus_wr_unit, m.wp_val as marcus_wp_val, m.wp_unit as marcus_wp_unit, m.lmbd_o_val as marcus_lmbd_o_val, m.lmbd_o_unit as marcus_lmbd_o_unit,
    
    t.alpha as troe_alpha, t.T3_val as troe_T3, t.T1_val as troe_T1, t.T2_val as troe_T2, 
    t.high_A_val as troe_high_A, t.high_n as troe_high_n, t.high_Ea_val as troe_high_Ea,
    t.low_A_val as troe_low_A, t.low_n as troe_low_n, t.low_Ea_val as troe_low_Ea,
    
    lind.high_A_val as lind_high_A, lind.high_n as lind_high_n, lind.high_Ea_val as lind_high_Ea,
    lind.low_A_val as lind_low_A, lind.low_n as lind_low_n, lind.low_Ea_val as lind_low_Ea,
    tb.low_A_val as tb_low_A, tb.low_n as tb_low_n, tb.low_Ea_val as tb_low_Ea,
    c.Tmin_val as cheb_Tmin, c.Pmin_val as cheb_Pmin, c.degreeT as cheb_degreeT, c.degreeP as cheb_degreeP,
    pd.id as pdep_id,
    ts.id as solute_ts_id
FROM kinetics_family_training_reactions_table r
JOIN kinetics_families_table f ON f.id = r.family_id
LEFT JOIN adj_reactions ar ON ar.training_reaction_id = r.id
LEFT JOIN kinetics_arrhenius_table a ON a.family_training_reaction_id = r.id
LEFT JOIN kinetics_arrhenius_ep_table ep ON ep.family_training_reaction_id = r.id
LEFT JOIN kinetics_arrhenius_bm_table bm ON bm.family_training_reaction_id = r.id
LEFT JOIN kinetics_marcus_table m ON m.family_training_reaction_id = r.id
LEFT JOIN kinetics_troe_table t ON t.family_training_reaction_id = r.id
LEFT JOIN kinetics_lindemann_table lind ON lind.family_training_reaction_id = r.id
LEFT JOIN kinetics_third_body_table tb ON tb.family_training_reaction_id = r.id
LEFT JOIN kinetics_chebyshev_table c ON c.family_training_reaction_id = r.id
LEFT JOIN kinetics_pdep_arrhenius_table pd ON pd.family_training_reaction_id = r.id
LEFT JOIN kinetics_solute_ts_diff_table ts ON ts.family_training_reaction_id = r.id
""")

all_family_rules_kinetics_view_sql = text("""CREATE VIEW all_family_rules_kinetics_view AS 
SELECT 
    f.name as family_name, r.id as rule_id, r.label, r.short_description, r.long_description, r.rank,
    
    COALESCE(
        a.kinetics_type, 
        ep.kinetics_type, 
        bm.kinetics_type,
        CASE WHEN m.id IS NOT NULL THEN 'Marcus' END,
        CASE WHEN t.id IS NOT NULL THEN 'Troe' END,
        CASE WHEN lind.id IS NOT NULL THEN 'Lindemann' END,
        CASE WHEN tb.id IS NOT NULL THEN 'ThirdBody' END,
        CASE WHEN c.id IS NOT NULL THEN 'Chebyshev' END,
        CASE WHEN pd.id IS NOT NULL THEN 'PDepArrhenius' END,
        CASE WHEN ts.id IS NOT NULL THEN 'SoluteTSDiffData' END
    ) AS overall_kinetics_type,

    a.A_val as arr_A_val, a.A_unit as arr_A_unit, a.n as arr_n, a.Ea_val as arr_Ea_val, a.Ea_unit as arr_Ea_unit, a.T0_val as arr_T0_val, a.T0_unit as arr_T0_unit,
    ep.alpha as ep_alpha, ep.E0_val as ep_E0_val, ep.E0_unit as ep_E0_unit,
    bm.w0_val as bm_w0_val, bm.w0_unit as bm_w0_unit, bm.E0_val as bm_E0_val, bm.E0_unit as bm_E0_unit,
    m.A_val as marcus_A_val, m.A_unit as marcus_A_unit, m.n as marcus_n, m.beta_val as marcus_beta_val, m.beta_unit as marcus_beta_unit, m.wr_val as marcus_wr_val, m.wr_unit as marcus_wr_unit, m.wp_val as marcus_wp_val, m.wp_unit as marcus_wp_unit, m.lmbd_o_val as marcus_lmbd_o_val, m.lmbd_o_unit as marcus_lmbd_o_unit,
    
    t.alpha as troe_alpha, t.T3_val as troe_T3, t.T1_val as troe_T1, t.T2_val as troe_T2, 
    t.high_A_val as troe_high_A, t.high_n as troe_high_n, t.high_Ea_val as troe_high_Ea,
    t.low_A_val as troe_low_A, t.low_n as troe_low_n, t.low_Ea_val as troe_low_Ea,
    
    lind.high_A_val as lind_high_A, lind.high_n as lind_high_n, lind.high_Ea_val as lind_high_Ea,
    lind.low_A_val as lind_low_A, lind.low_n as lind_low_n, lind.low_Ea_val as lind_low_Ea,
    tb.low_A_val as tb_low_A, tb.low_n as tb_low_n, tb.low_Ea_val as tb_low_Ea,
    c.Tmin_val as cheb_Tmin, c.Pmin_val as cheb_Pmin, c.degreeT as cheb_degreeT, c.degreeP as cheb_degreeP,
    pd.id as pdep_id,
    ts.id as solute_ts_id
FROM kinetics_family_rules_table r
JOIN kinetics_families_table f ON f.id = r.family_id
LEFT JOIN kinetics_arrhenius_table a ON a.family_rule_id = r.id
LEFT JOIN kinetics_arrhenius_ep_table ep ON ep.family_rule_id = r.id
LEFT JOIN kinetics_arrhenius_bm_table bm ON bm.family_rule_id = r.id
LEFT JOIN kinetics_marcus_table m ON m.family_rule_id = r.id
LEFT JOIN kinetics_troe_table t ON t.family_rule_id = r.id
LEFT JOIN kinetics_lindemann_table lind ON lind.family_rule_id = r.id
LEFT JOIN kinetics_third_body_table tb ON tb.family_rule_id = r.id
LEFT JOIN kinetics_chebyshev_table c ON c.family_rule_id = r.id
LEFT JOIN kinetics_pdep_arrhenius_table pd ON pd.family_rule_id = r.id
LEFT JOIN kinetics_solute_ts_diff_table ts ON ts.family_rule_id = r.id
""")

kinetics_library_dictionary_view_sql = text("""CREATE VIEW kinetics_library_dictionary_view AS
SELECT d.id, l.name as library_name, d.label, d.adjacency_list
FROM kinetics_library_dictionary_table d
JOIN kinetics_libraries_table l ON l.id = d.library_id
""")

kinetics_family_groups_view_sql = text("""CREATE VIEW kinetics_family_groups_view AS
SELECT g.id, f.name as family_name, g.label, g.group_adj_list, g.short_description, g.long_description
FROM kinetics_family_groups_table g
JOIN kinetics_families_table f ON f.id = g.family_id
""")

kinetics_family_forbidden_groups_view_sql = text("""CREATE VIEW kinetics_family_forbidden_groups_view AS
SELECT g.id, f.name as family_name, g.label, g.group_adj_list, g.short_description, g.long_description
FROM kinetics_family_forbidden_groups_table g
JOIN kinetics_families_table f ON f.id = g.family_id
""")

kinetics_family_training_dictionary_view_sql = text("""CREATE VIEW kinetics_family_training_dictionary_view AS
SELECT d.id, f.name as family_name, d.label, d.adjacency_list
FROM kinetics_family_training_dictionary_table d
JOIN kinetics_families_table f ON f.id = d.family_id
""")

kinetics_families_view_sql = text("""CREATE VIEW kinetics_families_view AS
SELECT f.id, f.name, f.short_description, f.long_description, f.template, f.recipe, f.reversible, f.reverse_map, f.reactant_num, f.product_num, f.auto_generated
FROM kinetics_families_table f
""")
