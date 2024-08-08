#!/usr/bin/env python
# encoding: utf-8

name = "halogens_G4"
shortDesc = "G4 (B3LYP/GTBas3)"
longDesc = """
Small halogenated species calculated with G4 method (B3LYP/GTBas3) using Gaussian 16
"""

entry(
    index=0,
    label="HF",
    molecule="""
1 F u0 p3 c0 {2,S}
2 H u0 p0 c0 {1,S}
""",
    statmech=Conformer(
        E0=(-282.308, "kJ/mol"),
        modes=[
            IdealGasTranslation(mass=(20.0062, "amu")),
        ],
    ),
    shortDesc="""B3LYP/GTBas3""",
    longDesc="""

""",
)

entry(
    index=1,
    label="HBr",
    molecule="""
1 Br u0 p3 c0 {2,S}
2 H  u0 p0 c0 {1,S}
""",
    statmech=Conformer(
        E0=(-42.7435, "kJ/mol"),
        modes=[
            IdealGasTranslation(mass=(79.9262, "amu")),
        ],
    ),
    shortDesc="""B3LYP/GTBas3""",
    longDesc="""

""",
)

entry(
    index=2,
    label="HCl",
    molecule="""
1 Cl u0 p3 c0 {2,S}
2 H  u0 p0 c0 {1,S}
""",
    statmech=Conformer(
        E0=(-99.1327, "kJ/mol"),
        modes=[
            IdealGasTranslation(mass=(35.9767, "amu")),
        ],
    ),
    shortDesc="""B3LYP/GTBas3""",
    longDesc="""

""",
)
