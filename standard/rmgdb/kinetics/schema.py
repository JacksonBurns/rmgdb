from sqlalchemy import Column, Integer, String, Float, ForeignKey, event, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column
from rmgdb.statmech.triggers import check_short_desc, delete_empty_desc

SCHEMA_BASE = declarative_base()

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
    
    # New keyword args
    allow_max_rate_violation = Column(Boolean)
    reversible = Column(Boolean)
    elementary_high_p = Column(Boolean)
    duplicate = Column(Boolean)

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
    
    # New keyword args
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

    # New keyword args
    allow_max_rate_violation = Column(Boolean)
    reversible = Column(Boolean)
    elementary_high_p = Column(Boolean)
    duplicate = Column(Boolean)

class KineticsData(SCHEMA_BASE):
    __tablename__ = "kinetics_data_table"
    id = Column(Integer, primary_key=True)
    library_reaction_id = mapped_column(ForeignKey("kinetics_library_reactions_table.id"))
    family_rule_id = mapped_column(ForeignKey("kinetics_family_rules_table.id"))
    family_training_reaction_id = mapped_column(ForeignKey("kinetics_family_training_reactions_table.id"))
    
    type = Column(String)
    A_val = Column(Float); A_unit = Column(String)
    n = Column(Float)
    Ea_val = Column(Float); Ea_unit = Column(String)
    T0_val = Column(Float); T0_unit = Column(String)
    w0_val = Column(Float); w0_unit = Column(String)
    E0_val = Column(Float); E0_unit = Column(String)
    Tmin_val = Column(Float); Tmin_unit = Column(String)
    Tmax_val = Column(Float); Tmax_unit = Column(String)
    comment = Column(String)
    
    # Catch-all for complex models (Chebyshev arrays, Troe parameters, MultiArrhenius lists, etc.)
    raw_data = Column(String)

for table in [KineticsLibraries, KineticsLibraryReactions, KineticsFamilies, KineticsFamilyGroups, KineticsFamilyRules, KineticsFamilyTrainingReactions]:
    event.listen(table, "before_insert", check_short_desc)
    event.listen(table, "before_insert", delete_empty_desc)
