from sqlalchemy import select, text

from rmgdb.statmech.schema import Conformer, IdealGasTranslation, NonlinearRotor, LinearRotor, HarmonicOscillator, StatmechLibraries

# we can either manually specify the entire SQL statement in plain text
statmech_groups_view_sql = text("""CREATE VIEW statmech_groups_view AS select 
groups_table.name, groups_table.short_description, groups_table.long_description, groups_table.label, groups_table."group",
group_frequency_table.symmetry,
frequency_table."lower", frequency_table."upper", frequency_table.degeneracy from groups_table
LEFT JOIN group_frequency_table on group_frequency_table.parent_id == groups_table.id
LEFT JOIN frequency_table on frequency_table.parent_id == group_frequency_table.id""")

label_pairs_view_sql = text("""create view label_pairs_view as select parent_lookup.label as parent_label, child_lookup.label as child_label from groups_tree_table
join groups_table child_lookup on child_lookup.id == groups_tree_table.child_id
join groups_table parent_lookup on parent_lookup.id == groups_tree_table.parent_id""")


# or assemble it using Python
conformer_view = (
    select(
        Conformer.parent_id.label("parent_id"),
        Conformer.energy.label("energy"),
        Conformer.energy_unit.label("energy_unit"),
        Conformer.spin_multiplicity.label("spin_multiplicity"),
        Conformer.optical_isomers.label("optical_isomers"),
        IdealGasTranslation.mass.label("mass"),
        IdealGasTranslation.mass_unit.label("mass_unit"),
        NonlinearRotor.inertia_x.label("inertia_x"),
        NonlinearRotor.inertia_y.label("inertia_y"),
        NonlinearRotor.inertia_z.label("inertia_z"),
        NonlinearRotor.inertia_unit.label("nonlinear_inertia_unit"),
        NonlinearRotor.symmetry.label("nonlinear_symmetry"),
        LinearRotor.inertia.label("linear_inertia"),
        LinearRotor.inertia_unit.label("linear_inertia_unit"),
        LinearRotor.symmetry.label("linear_symmetry"),
        HarmonicOscillator.freq_unit.label("harmonic_freq_unit"),
        HarmonicOscillator.freq_1.label("harmonic_freq_1"),
        HarmonicOscillator.freq_2.label("harmonic_freq_2"),
        HarmonicOscillator.freq_3.label("harmonic_freq_3"),
        HarmonicOscillator.freq_4.label("harmonic_freq_4"),
        HarmonicOscillator.freq_5.label("harmonic_freq_5"),
        HarmonicOscillator.freq_6.label("harmonic_freq_6"),
        HarmonicOscillator.freq_7.label("harmonic_freq_7"),
        HarmonicOscillator.freq_8.label("harmonic_freq_8"),
        HarmonicOscillator.freq_9.label("harmonic_freq_9"),
        HarmonicOscillator.freq_10.label("harmonic_freq_10"),
        HarmonicOscillator.freq_11.label("harmonic_freq_11"),
        HarmonicOscillator.freq_12.label("harmonic_freq_12"),
    )
    .select_from(
        Conformer,
    )
    .outerjoin(
        NonlinearRotor,
        # sqlalchemy should infer this auto-magically from the FK relationship
        # we give it anyway to make this relationship more explicit
        Conformer.id == NonlinearRotor.parent_id,
    )
    .outerjoin(
        LinearRotor,
        Conformer.id == LinearRotor.parent_id,
    )
    .outerjoin(
        HarmonicOscillator,
        Conformer.id == HarmonicOscillator.parent_id,
    )
    .outerjoin(
        IdealGasTranslation,
        Conformer.id == IdealGasTranslation.parent_id,
    )
).subquery("inner_t")


view_query = (
    select(
        StatmechLibraries.id,
        StatmechLibraries.name,
        StatmechLibraries.short_description,
        StatmechLibraries.long_description,
        StatmechLibraries.label,
        StatmechLibraries.adjacency_list,
        conformer_view.c.energy,
        conformer_view.c.energy_unit,
        conformer_view.c.spin_multiplicity,
        conformer_view.c.optical_isomers,
        conformer_view.c.mass,
        conformer_view.c.mass_unit,
        conformer_view.c.inertia_x,
        conformer_view.c.inertia_y,
        conformer_view.c.inertia_z,
        conformer_view.c.nonlinear_inertia_unit,
        conformer_view.c.nonlinear_symmetry,
        conformer_view.c.linear_inertia,
        conformer_view.c.linear_inertia_unit,
        conformer_view.c.linear_symmetry,
        conformer_view.c.harmonic_freq_unit,
        conformer_view.c.harmonic_freq_1,
        conformer_view.c.harmonic_freq_2,
        conformer_view.c.harmonic_freq_3,
        conformer_view.c.harmonic_freq_4,
        conformer_view.c.harmonic_freq_5,
        conformer_view.c.harmonic_freq_6,
        conformer_view.c.harmonic_freq_7,
        conformer_view.c.harmonic_freq_8,
        conformer_view.c.harmonic_freq_9,
        conformer_view.c.harmonic_freq_10,
        conformer_view.c.harmonic_freq_11,
        conformer_view.c.harmonic_freq_12,
    )
    .select_from(
        conformer_view,
    )
    .outerjoin(
        StatmechLibraries,
        StatmechLibraries.id == conformer_view.c.parent_id,
    )
)

# Create the view in the database
view_name = "statmech_libraries_view"
statmech_libraries_view_sql = text(f"CREATE VIEW {view_name} AS {view_query}")
