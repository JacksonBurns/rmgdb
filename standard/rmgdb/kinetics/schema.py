from sqlalchemy import Column, Integer, String, Float, ForeignKey, event, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column
from rmgdb.statmech.triggers import check_short_desc, delete_empty_desc

SCHEMA_BASE = declarative_base()

# ---------------------------------------------------------
# Core Hierarchies
# ---------------------------------------------------------
class KineticsLibraries(SCHEMA_BASE):
    __tablename__ = "kinetics_libraries_table"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)

class KineticsLibraryDictionary(SCHEMA_BASE):
    __tablename__ = "kinetics_library_dictionary_table"
    id = Column(Integer, primary_key=True)
    library_id = mapped_column(ForeignKey("kinetics_libraries_table.id"))
    label = Column(String)
    adjacency_list = Column(String)

class KineticsLibraryReactions(SCHEMA_BASE):
    __tablename__ = "kinetics_library_reactions_table"
    id = Column(Integer, primary_key=True)
    library_id = mapped_column(ForeignKey("kinetics_libraries_table.id"))
    label = Column(String)
    degeneracy = Column(Float)
    short_description = Column(String)
    long_description = Column(String)
    rank = Column(Integer)
    allow_max_rate_violation = Column(Boolean)
    reversible = Column(Boolean)
    elementary_high_p = Column(Boolean)
    duplicate = Column(Boolean)

class KineticsLibraryReactionSpecies(SCHEMA_BASE):
    __tablename__ = "kinetics_library_reaction_species_table"
    id = Column(Integer, primary_key=True)
    library_reaction_id = mapped_column(ForeignKey("kinetics_library_reactions_table.id"))
    species_label = Column(String)
    role = Column(String)  # 'reactant' or 'product'

class KineticsFamilies(SCHEMA_BASE):
    __tablename__ = "kinetics_families_table"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    template = Column(String)
    recipe = Column(String)
    reversible = Column(Boolean)
    reverse_map = Column(String)
    reactant_num = Column(Integer)
    product_num = Column(Integer)
    auto_generated = Column(Boolean)

class KineticsFamilyGroups(SCHEMA_BASE):
    __tablename__ = "kinetics_family_groups_table"
    id = Column(Integer, primary_key=True)
    family_id = mapped_column(ForeignKey("kinetics_families_table.id"))
    label = Column(String)
    group_adj_list = Column(String)
    short_description = Column(String)
    long_description = Column(String)

class KineticsFamilyForbiddenGroups(SCHEMA_BASE):
    __tablename__ = "kinetics_family_forbidden_groups_table"
    id = Column(Integer, primary_key=True)
    family_id = mapped_column(ForeignKey("kinetics_families_table.id"))
    label = Column(String)
    group_adj_list = Column(String)
    short_description = Column(String)
    long_description = Column(String)

class KineticsFamilyGroupsTree(SCHEMA_BASE):
    __tablename__ = "kinetics_family_groups_tree_table"
    id = Column(Integer, primary_key=True)
    parent_id = mapped_column(ForeignKey("kinetics_family_groups_table.id"))
    child_id = mapped_column(ForeignKey("kinetics_family_groups_table.id"))

class KineticsFamilyRules(SCHEMA_BASE):
    __tablename__ = "kinetics_family_rules_table"
    id = Column(Integer, primary_key=True)
    family_id = mapped_column(ForeignKey("kinetics_families_table.id"))
    label = Column(String)
    short_description = Column(String)
    long_description = Column(String)
    rank = Column(Integer)
    allow_max_rate_violation = Column(Boolean)
    reversible = Column(Boolean)
    elementary_high_p = Column(Boolean)
    duplicate = Column(Boolean)

class KineticsFamilyTrainingDictionary(SCHEMA_BASE):
    __tablename__ = "kinetics_family_training_dictionary_table"
    id = Column(Integer, primary_key=True)
    family_id = mapped_column(ForeignKey("kinetics_families_table.id"))
    label = Column(String)
    adjacency_list = Column(String)

class KineticsFamilyTrainingReactions(SCHEMA_BASE):
    __tablename__ = "kinetics_family_training_reactions_table"
    id = Column(Integer, primary_key=True)
    family_id = mapped_column(ForeignKey("kinetics_families_table.id"))
    label = Column(String)
    degeneracy = Column(Float)
    short_description = Column(String)
    long_description = Column(String)
    rank = Column(Integer)
    allow_max_rate_violation = Column(Boolean)
    reversible = Column(Boolean)
    elementary_high_p = Column(Boolean)
    duplicate = Column(Boolean)

class KineticsFamilyTrainingReactionSpecies(SCHEMA_BASE):
    __tablename__ = "kinetics_family_training_reaction_species_table"
    id = Column(Integer, primary_key=True)
    training_reaction_id = mapped_column(ForeignKey("kinetics_family_training_reactions_table.id"))
    species_label = Column(String)
    role = Column(String)

# ---------------------------------------------------------
# Sub-Kinetics Tables (Explicit Models)
# ---------------------------------------------------------
class KineticsArrhenius(SCHEMA_BASE):
    __tablename__ = "kinetics_arrhenius_table"
    id = Column(Integer, primary_key=True)
    library_reaction_id = mapped_column(ForeignKey("kinetics_library_reactions_table.id"))
    family_rule_id = mapped_column(ForeignKey("kinetics_family_rules_table.id"))
    family_training_reaction_id = mapped_column(ForeignKey("kinetics_family_training_reactions_table.id"))
    kinetics_type = Column(String)
    A_val = Column(Float); A_unit = Column(String); n = Column(Float)
    Ea_val = Column(Float); Ea_unit = Column(String)
    T0_val = Column(Float); T0_unit = Column(String)
    Tmin_val = Column(Float); Tmin_unit = Column(String)
    Tmax_val = Column(Float); Tmax_unit = Column(String)
    comment = Column(String)

class KineticsArrheniusEP(SCHEMA_BASE):
    __tablename__ = "kinetics_arrhenius_ep_table"
    id = Column(Integer, primary_key=True)
    library_reaction_id = mapped_column(ForeignKey("kinetics_library_reactions_table.id"))
    family_rule_id = mapped_column(ForeignKey("kinetics_family_rules_table.id"))
    family_training_reaction_id = mapped_column(ForeignKey("kinetics_family_training_reactions_table.id"))
    kinetics_type = Column(String)
    A_val = Column(Float); A_unit = Column(String); n = Column(Float)
    alpha = Column(Float)
    E0_val = Column(Float); E0_unit = Column(String)
    Tmin_val = Column(Float); Tmin_unit = Column(String)
    Tmax_val = Column(Float); Tmax_unit = Column(String)
    comment = Column(String)

class KineticsArrheniusBM(SCHEMA_BASE):
    __tablename__ = "kinetics_arrhenius_bm_table"
    id = Column(Integer, primary_key=True)
    library_reaction_id = mapped_column(ForeignKey("kinetics_library_reactions_table.id"))
    family_rule_id = mapped_column(ForeignKey("kinetics_family_rules_table.id"))
    family_training_reaction_id = mapped_column(ForeignKey("kinetics_family_training_reactions_table.id"))
    kinetics_type = Column(String)
    A_val = Column(Float); A_unit = Column(String); n = Column(Float)
    w0_val = Column(Float); w0_unit = Column(String)
    E0_val = Column(Float); E0_unit = Column(String)
    Tmin_val = Column(Float); Tmin_unit = Column(String)
    Tmax_val = Column(Float); Tmax_unit = Column(String)
    comment = Column(String)

class KineticsMarcus(SCHEMA_BASE):
    __tablename__ = "kinetics_marcus_table"
    id = Column(Integer, primary_key=True)
    library_reaction_id = mapped_column(ForeignKey("kinetics_library_reactions_table.id"))
    family_rule_id = mapped_column(ForeignKey("kinetics_family_rules_table.id"))
    family_training_reaction_id = mapped_column(ForeignKey("kinetics_family_training_reactions_table.id"))
    A_val = Column(Float); A_unit = Column(String); n = Column(Float)
    beta_val = Column(Float); beta_unit = Column(String)
    wr_val = Column(Float); wr_unit = Column(String)
    wp_val = Column(Float); wp_unit = Column(String)
    lmbd_o_val = Column(Float); lmbd_o_unit = Column(String)
    comment = Column(String)

class KineticsMarcusCoefs(SCHEMA_BASE):
    __tablename__ = "kinetics_marcus_coefs_table"
    id = Column(Integer, primary_key=True)
    marcus_id = mapped_column(ForeignKey("kinetics_marcus_table.id"))
    coef_index = Column(Integer)
    coeff_value = Column(Float)

class KineticsTroe(SCHEMA_BASE):
    __tablename__ = "kinetics_troe_table"
    id = Column(Integer, primary_key=True)
    library_reaction_id = mapped_column(ForeignKey("kinetics_library_reactions_table.id"))
    family_rule_id = mapped_column(ForeignKey("kinetics_family_rules_table.id"))
    family_training_reaction_id = mapped_column(ForeignKey("kinetics_family_training_reactions_table.id"))
    alpha = Column(Float)
    T3_val = Column(Float); T3_unit = Column(String)
    T1_val = Column(Float); T1_unit = Column(String)
    T2_val = Column(Float); T2_unit = Column(String)
    high_A_val = Column(Float); high_A_unit = Column(String); high_n = Column(Float); high_Ea_val = Column(Float); high_Ea_unit = Column(String)
    low_A_val = Column(Float); low_A_unit = Column(String); low_n = Column(Float); low_Ea_val = Column(Float); low_Ea_unit = Column(String)
    Tmin_val = Column(Float); Tmin_unit = Column(String)
    Tmax_val = Column(Float); Tmax_unit = Column(String)
    comment = Column(String)

class KineticsLindemann(SCHEMA_BASE):
    __tablename__ = "kinetics_lindemann_table"
    id = Column(Integer, primary_key=True)
    library_reaction_id = mapped_column(ForeignKey("kinetics_library_reactions_table.id"))
    family_rule_id = mapped_column(ForeignKey("kinetics_family_rules_table.id"))
    family_training_reaction_id = mapped_column(ForeignKey("kinetics_family_training_reactions_table.id"))
    high_A_val = Column(Float); high_A_unit = Column(String); high_n = Column(Float); high_Ea_val = Column(Float); high_Ea_unit = Column(String)
    low_A_val = Column(Float); low_A_unit = Column(String); low_n = Column(Float); low_Ea_val = Column(Float); low_Ea_unit = Column(String)
    Tmin_val = Column(Float); Tmin_unit = Column(String)
    Tmax_val = Column(Float); Tmax_unit = Column(String)
    comment = Column(String)

class KineticsThirdBody(SCHEMA_BASE):
    __tablename__ = "kinetics_third_body_table"
    id = Column(Integer, primary_key=True)
    library_reaction_id = mapped_column(ForeignKey("kinetics_library_reactions_table.id"))
    family_rule_id = mapped_column(ForeignKey("kinetics_family_rules_table.id"))
    family_training_reaction_id = mapped_column(ForeignKey("kinetics_family_training_reactions_table.id"))
    low_A_val = Column(Float); low_A_unit = Column(String); low_n = Column(Float); low_Ea_val = Column(Float); low_Ea_unit = Column(String)
    Tmin_val = Column(Float); Tmin_unit = Column(String)
    Tmax_val = Column(Float); Tmax_unit = Column(String)
    comment = Column(String)

class KineticsEfficiencies(SCHEMA_BASE):
    __tablename__ = "kinetics_efficiencies_table"
    id = Column(Integer, primary_key=True)
    library_reaction_id = mapped_column(ForeignKey("kinetics_library_reactions_table.id"))
    family_rule_id = mapped_column(ForeignKey("kinetics_family_rules_table.id"))
    family_training_reaction_id = mapped_column(ForeignKey("kinetics_family_training_reactions_table.id"))
    species_label = Column(String)
    efficiency = Column(Float)

class KineticsChebyshev(SCHEMA_BASE):
    __tablename__ = "kinetics_chebyshev_table"
    id = Column(Integer, primary_key=True)
    library_reaction_id = mapped_column(ForeignKey("kinetics_library_reactions_table.id"))
    family_rule_id = mapped_column(ForeignKey("kinetics_family_rules_table.id"))
    family_training_reaction_id = mapped_column(ForeignKey("kinetics_family_training_reactions_table.id"))
    Tmin_val = Column(Float); Tmin_unit = Column(String); Tmax_val = Column(Float); Tmax_unit = Column(String)
    Pmin_val = Column(Float); Pmin_unit = Column(String); Pmax_val = Column(Float); Pmax_unit = Column(String)
    degreeT = Column(Integer); degreeP = Column(Integer)
    comment = Column(String)

class KineticsChebyshevCoeffs(SCHEMA_BASE):
    __tablename__ = "kinetics_chebyshev_coeffs_table"
    id = Column(Integer, primary_key=True)
    chebyshev_id = mapped_column(ForeignKey("kinetics_chebyshev_table.id"))
    t_index = Column(Integer)
    p_index = Column(Integer)
    coeff_value = Column(Float)

class KineticsPDepArrhenius(SCHEMA_BASE):
    __tablename__ = "kinetics_pdep_arrhenius_table"
    id = Column(Integer, primary_key=True)
    library_reaction_id = mapped_column(ForeignKey("kinetics_library_reactions_table.id"))
    family_rule_id = mapped_column(ForeignKey("kinetics_family_rules_table.id"))
    family_training_reaction_id = mapped_column(ForeignKey("kinetics_family_training_reactions_table.id"))
    Tmin_val = Column(Float); Tmin_unit = Column(String); Tmax_val = Column(Float); Tmax_unit = Column(String)
    comment = Column(String)

class KineticsPDepArrheniusPressures(SCHEMA_BASE):
    __tablename__ = "kinetics_pdep_arrhenius_pressures_table"
    id = Column(Integer, primary_key=True)
    pdep_id = mapped_column(ForeignKey("kinetics_pdep_arrhenius_table.id"))
    P_val = Column(Float); P_unit = Column(String)
    A_val = Column(Float); A_unit = Column(String); n = Column(Float)
    Ea_val = Column(Float); Ea_unit = Column(String)

class KineticsSoluteTSDiff(SCHEMA_BASE):
    __tablename__ = "kinetics_solute_ts_diff_table"
    id = Column(Integer, primary_key=True)
    library_reaction_id = mapped_column(ForeignKey("kinetics_library_reactions_table.id"))
    family_rule_id = mapped_column(ForeignKey("kinetics_family_rules_table.id"))
    family_training_reaction_id = mapped_column(ForeignKey("kinetics_family_training_reactions_table.id"))
    S_g = Column(Float); B_g = Column(Float); E_g = Column(Float)
    L_g = Column(Float); A_g = Column(Float); K_g = Column(Float)
    S_h = Column(Float); B_h = Column(Float); E_h = Column(Float)
    L_h = Column(Float); A_h = Column(Float); K_h = Column(Float)
    Tmin_val = Column(Float); Tmin_unit = Column(String)
    Tmax_val = Column(Float); Tmax_unit = Column(String)
    Pmin_val = Column(Float); Pmin_unit = Column(String)
    Pmax_val = Column(Float); Pmax_unit = Column(String)
    comment = Column(String)

for table in [KineticsLibraries, KineticsLibraryReactions, KineticsFamilies, KineticsFamilyGroups, KineticsFamilyForbiddenGroups, KineticsFamilyRules, KineticsFamilyTrainingReactions]:
    event.listen(table, "before_insert", check_short_desc)
    event.listen(table, "before_insert", delete_empty_desc)
