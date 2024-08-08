from schema import (
    GroupsTable,
    GroupsTreeTable,
    IdealGasTranslationTable,
    FrequencyTable,
    StatmechLibrariesTable,
    ConformerTable,
    NonlinearRotorTable,
    HarmonicOscillatorTable,
)


from sqlalchemy import create_engine, Column, Integer, String, Numeric, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from schema import Base


# Create engine and session
engine = create_engine("sqlite:///demo.db", echo=True)
Session = sessionmaker(bind=engine)
session = Session()


Base.metadata.create_all(engine)


# exec() the actual library file, spoofing the classnames and args to map to database rows...


# Map a couple example groups into the database
# entry(
#     index = 0,
#     label = "R!H!Val7",
#     group = "OR{R!H!Val7x0, R!H!Val7x1, R!H!Val7x2_trip, R!H!Val7x3_quart}",
#     statmech = None,
#     shortDesc = """""",
#     longDesc =
# """

# """,
# )
new_group = GroupsTable(
    id=0,
    short_description="",
    long_description="",
    label="R!H!Val7",
    group="OR{R!H!Val7x0, R!H!Val7x1, R!H!Val7x2_trip, R!H!Val7x3_quart}",
    symmetry=None,
)
session.add(new_group)

# entry(
#     index = 205,
#     label = "Cd-Cl1sCl1sCd_399",
#     group =
# """
# 1 * Cd   u0 {2,S} {3,S} {4,D}
# 2   Cl1s u0 {1,S}
# 3   Cl1s u0 {1,S}
# 4   Cd   ux {1,D}
# """,
#     statmech = GroupFrequencies(
#         frequencies = [
#             (123, 183, 1),
#             (146, 312, 1),
#             (236, 324, 1),
#             (397, 525, 1),
#             (593, 693, 1),
#             (1004, 1190, 1),
#         ],
#         symmetry = 1,
#     ),
#     shortDesc = """""",
#     longDesc =
# """
#
# """,
# )
new_group = GroupsTable(
    id=205,
    short_description="",
    long_description="",
    label="Cd-Cl1sCl1sCd_399",
    group="""
1 * Cd   u0 {2,S} {3,S} {4,D}
2   Cl1s u0 {1,S}
3   Cl1s u0 {1,S}
4   Cd   ux {1,D}
""",
    symmetry=1,
)
session.add(new_group)

# pretend that these are paired in the tree, map them together
new_pair = GroupsTreeTable(
    id=0,
    parent_id=0,
    child_id=205,
)
session.add(new_pair)

# add the other data for this group to the corresponding table
new_frequency = FrequencyTable(
    id=0,
    parent_id=205,
    frequency_part_1=123,
    frequency_part_2=183,
    frequency_part_3=1,
)
session.add(new_frequency)
new_frequency = FrequencyTable(
    id=1,
    parent_id=205,
    frequency_part_1=146,
    frequency_part_2=312,
    frequency_part_3=1,
)
session.add(new_frequency)

# now map the libraries in
# entry(
#     index=51,
#     label="Cl[CH]Br",
#     molecule="""
# multiplicity 2
# 1 Br u0 p3 c0 {3,S}
# 2 Cl u0 p3 c0 {3,S}
# 3 C  u1 p0 c0 {1,S} {2,S} {4,S}
# 4 H  u0 p0 c0 {3,S}
# """,
#     statmech=Conformer(
#         E0=(126.863, "kJ/mol"),
#         modes=[
#             IdealGasTranslation(mass=(126.895, "amu")),
#             NonlinearRotor(inertia=([11.8295, 238.782, 250.25], "amu*angstrom^2"), symmetry=1),
#             HarmonicOscillator(frequencies=([241.769, 449.78, 664.437, 843.488, 1202.56, 3218.64], "cm^-1")),
#         ],
#         spin_multiplicity=2,
#         optical_isomers=2,
#     ),
#     shortDesc="""B3LYP/GTBas3""",
#     longDesc="""
#
# """,
# )
new_library_entry = StatmechLibrariesTable(
    id=51,
    name="halogens_G4",
    short_description="B3LYP/GTBas3",
    long_description="",
    label="Cl[CH]Br",
    adjacency_list="""
multiplicity 2
1 Br u0 p3 c0 {3,S}
2 Cl u0 p3 c0 {3,S}
3 C  u1 p0 c0 {1,S} {2,S} {4,S}
4 H  u0 p0 c0 {3,S}
""",
)
session.add(new_library_entry)

new_conformer = ConformerTable(
    id=0,
    parent_id=51,
    energy=126.863,
    energy_unit="kJ/mol",
    spin_multiplicity=2,
    optical_isomers=2,
)
session.add(new_conformer)


new_igt = IdealGasTranslationTable(
    id=0,
    parent_id=0,
    mass=126.895,
    mass_unit="amu",
)
session.add(new_igt)


try:
    session.commit()
except ValueError as e:
    session.rollback()
    print(f"Error: {e}")

session.close()
