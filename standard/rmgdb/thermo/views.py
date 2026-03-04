from sqlalchemy import text

# --------------------------------------------------------------------------------
# Group Tree Label Pairs
# --------------------------------------------------------------------------------
label_pairs_view_sql = text("""CREATE VIEW label_pairs_view AS 
SELECT 
    parent_lookup.label as parent_label, 
    child_lookup.label as child_label 
FROM groups_tree_table
JOIN groups_table child_lookup on child_lookup.id == groups_tree_table.child_id
JOIN groups_table parent_lookup on parent_lookup.id == groups_tree_table.parent_id
""")

# --------------------------------------------------------------------------------
# Thermo Libraries Flat View
# --------------------------------------------------------------------------------
thermo_libraries_view_sql = text("""CREATE VIEW thermo_libraries_view AS 
SELECT 
    l.id, l.name, l.short_description, l.long_description, l.label, l.adjacency_list,
    
    td.Tdata_unit, td.Cpdata_unit, td.H298, td.H298_unit, td.S298, td.S298_unit,
    td.Tdata_1, td.Tdata_2, td.Tdata_3, td.Tdata_4, td.Tdata_5, td.Tdata_6, td.Tdata_7,
    td.Cpdata_1, td.Cpdata_2, td.Cpdata_3, td.Cpdata_4, td.Cpdata_5, td.Cpdata_6, td.Cpdata_7,
    
    n.Tmin AS nasa_Tmin, n.Tmax AS nasa_Tmax, n.T_unit AS nasa_T_unit,
    n.E0, n.E0_unit, n.Cp0, n.Cp0_unit, n.CpInf, n.CpInf_unit,
    
    np.c1, np.c2, np.c3, np.c4, np.c5, np.c6, np.c7,
    np.Tmin AS poly_Tmin, np.Tmax AS poly_Tmax, np.T_unit AS poly_T_unit

FROM thermo_libraries_table l
LEFT JOIN thermo_data_table td ON td.library_parent_id = l.id
LEFT JOIN nasa_table n ON n.library_parent_id = l.id
LEFT JOIN nasa_polynomial_table np ON np.nasa_id = n.id
""")

# --------------------------------------------------------------------------------
# Thermo Depositories Flat View
# --------------------------------------------------------------------------------
thermo_depositories_view_sql = text("""CREATE VIEW thermo_depositories_view AS 
SELECT 
    d.id, d.name, d.short_description, d.long_description, d.label, d.adjacency_list,
    
    td.Tdata_unit, td.Cpdata_unit, td.H298, td.H298_unit, td.S298, td.S298_unit,
    td.Tdata_1, td.Tdata_2, td.Tdata_3, td.Tdata_4, td.Tdata_5, td.Tdata_6, td.Tdata_7,
    td.Cpdata_1, td.Cpdata_2, td.Cpdata_3, td.Cpdata_4, td.Cpdata_5, td.Cpdata_6, td.Cpdata_7,
    
    n.Tmin AS nasa_Tmin, n.Tmax AS nasa_Tmax, n.T_unit AS nasa_T_unit,
    n.E0, n.E0_unit, n.Cp0, n.Cp0_unit, n.CpInf, n.CpInf_unit,
    
    np.c1, np.c2, np.c3, np.c4, np.c5, np.c6, np.c7,
    np.Tmin AS poly_Tmin, np.Tmax AS poly_Tmax, np.T_unit AS poly_T_unit

FROM thermo_depositories_table d
LEFT JOIN thermo_data_table td ON td.depository_parent_id = d.id
LEFT JOIN nasa_table n ON n.depository_parent_id = d.id
LEFT JOIN nasa_polynomial_table np ON np.nasa_id = n.id
""")

# --------------------------------------------------------------------------------
# Thermo Groups Flat View
# --------------------------------------------------------------------------------
thermo_groups_view_sql = text("""CREATE VIEW thermo_groups_view AS 
SELECT 
    g.id, g.name, g.short_description, g.long_description, g.label, g."group",
    
    td.Tdata_unit, td.Cpdata_unit, td.H298, td.H298_unit, td.S298, td.S298_unit,
    td.Tdata_1, td.Tdata_2, td.Tdata_3, td.Tdata_4, td.Tdata_5, td.Tdata_6, td.Tdata_7,
    td.Cpdata_1, td.Cpdata_2, td.Cpdata_3, td.Cpdata_4, td.Cpdata_5, td.Cpdata_6, td.Cpdata_7,
    
    n.Tmin AS nasa_Tmin, n.Tmax AS nasa_Tmax, n.T_unit AS nasa_T_unit,
    n.E0, n.E0_unit, n.Cp0, n.Cp0_unit, n.CpInf, n.CpInf_unit,
    
    np.c1, np.c2, np.c3, np.c4, np.c5, np.c6, np.c7,
    np.Tmin AS poly_Tmin, np.Tmax AS poly_Tmax, np.T_unit AS poly_T_unit

FROM groups_table g
LEFT JOIN thermo_data_table td ON td.group_parent_id = g.id
LEFT JOIN nasa_table n ON n.group_parent_id = g.id
LEFT JOIN nasa_polynomial_table np ON np.nasa_id = n.id
""")
