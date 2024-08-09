import json

import pandas as pd

QUERY = "SELECT * FROM statmech_libraries_view"

statmech_df = pd.read_sql(QUERY, "sqlite:///demo_v2.db")

DUMP_FILE = 'demo_v2.json'

all_rows = []
for _, row in statmech_df.iterrows():
    formatted_dict = dict(
        # don't keep the internal database id in the text dump
        # id=row.id
        name=row.name,
        short_description=row.short_description,
        long_description=row.long_description,
        label=row.label,
        adjacency_list=row.adjacency_list,
        statmech=dict(
            energy=row.energy,
            modes=dict(
                ideal_gas_translation=dict(
                    mass=row.mass,
                    mass_unit=row.mass_unit,
                ),
                nonlinear_rotor=dict(
                    inertia_x=row.inertia_x,
                    inertia_y=row.inertia_y,
                    inertia_z=row.inertia_z,
                    nonlinear_inertia_unit=row.nonlinear_inertia_unit,
                    nonlinear_symmetry=row.nonlinear_symmetry,
                ),
                linear_rotor=dict(
                    linear_inertia=row.linear_inertia,
                    linear_inertia_unit=row.linear_inertia_unit,
                    linear_symmetry=row.linear_symmetry,
                ),
                harmonic_oscillator=dict(
                    harmonic_freq_unit=row.harmonic_freq_unit,
                    harmonic_freq_1=row.harmonic_freq_1,
                ),
            ),
        ),
    )
    all_rows.append(formatted_dict)

with open(DUMP_FILE, 'w', encoding='utf-8') as f:
    json.dump(all_rows, f, ensure_ascii=False, indent=4)

with open(DUMP_FILE, 'r', encoding='utf-8') as f:
    all_rows = json.load(f)

entry_counter = 0
statmech_counter = 0
ideal_gas_counter = 0
nonlinear_rotor_counter = 0
linear_rotor_counter = 0
harmonic_oscillator_counter = 0
for row in all_rows:
    # do the inverse mapping, still with counters to rebuild the internal index
    
    if row.get('ideal_gas', False):
        parent_id = entry_counter
        ...
        ideal_gas_counter += 1
    entry_counter += 1

