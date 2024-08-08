# for accessing the database from RMG, just use views to compile together common tables
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Numeric, select, text

from schema import ConformerTable, StatmechLibrariesTable, IdealGasTranslationTable, Base
from sqlalchemy.orm import sessionmaker

# Create engine and connect to database
engine = create_engine("sqlite:///demo.db", echo=True)


# select * from statmech_libraries_table
# join (
#  select conformer_table.parent_id, energy, energy_unit, spin_multiplicity, optical_isomers, mass, mass_unit from
#  conformer_table join ideal_gas_translation_table on conformer_table.id = ideal_gas_translation_table.parent_id) as temp_t
#  on statmech_libraries_table.id = temp_t.parent_id

inner_query = (
    select(
        ConformerTable.parent_id.label("parent_id"),
        ConformerTable.energy.label("energy"),
        ConformerTable.energy_unit.label("energy_unit"),
        ConformerTable.spin_multiplicity.label("spin_multiplicity"),
        ConformerTable.optical_isomers.label("optical_isomers"),
        IdealGasTranslationTable.mass.label("mass"),
        IdealGasTranslationTable.mass_unit.label("mass_unit"),
    )
    .select_from(
        ConformerTable,
    )
    .join(
        IdealGasTranslationTable,
        ConformerTable.id == IdealGasTranslationTable.parent_id,  # sqlalchemy should infer this auto-magically from the FK relationship
    )
).subquery("inner_t")

print(inner_query)
print()

view_query = (
    select(
        StatmechLibrariesTable.id,
        StatmechLibrariesTable.name,
        StatmechLibrariesTable.short_description,
        StatmechLibrariesTable.long_description,
        StatmechLibrariesTable.label,
        StatmechLibrariesTable.adjacency_list,
        inner_query.c.energy,
        inner_query.c.energy_unit,
        inner_query.c.spin_multiplicity,
        inner_query.c.optical_isomers,
        inner_query.c.mass,
        inner_query.c.mass_unit,
    ).select_from(
        inner_query,
    ).join(
        StatmechLibrariesTable,
        StatmechLibrariesTable.id == inner_query.c.parent_id,
    )
)
#     StatmechLibrariesTable.join(
#         ConformerTable.join(
#             IdealGasTranslationTable,
#             ConformerTable.id == IdealGasTranslationTable.parent_id
#         ),
#         StatmechLibrariesTable.id == ConformerTable.parent_id
#     )
# )

print(view_query)
print()

# Create the view in the database
view_name = "statmech_libraries_view"
create_view_sql = text(f"CREATE VIEW {view_name} AS {view_query}")

Session = sessionmaker(bind=engine)
session = Session()
session.execute(create_view_sql)
