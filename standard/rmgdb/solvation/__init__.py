"""
RMG Solvation Database Module

This module provides database functionality for solvation data including:
- Abraham solute parameters (S, B, E, L, A, V)
- Abraham and Mintz solvent parameters for solvation free energy and enthalpy
- Viscosity parameters and additional solvent properties
- Group-based solvation contributions
- Data quality metrics and validation

Classes:
    Groups: Chemical groups with solvation contributions
    SoluteLibrary: Library of solute molecules with solvation data
    SolventLibrary: Library of solvents with comprehensive parameters
    SoluteData: Abraham parameters for solutes or groups
    SolventData: Complete solvent parameter set
    DataCountSolvent: Data quality metrics for solvent parameters
"""

from .schema import (
    SCHEMA_BASE,
    Groups,
    GroupsTree,
    SolvationLibraries,
    SoluteLibrary,
    SolventLibrary,
    SoluteData,
    SolventData,
    DataCountGAV,
    DataCountSolvent,
)

from .views import (
    solvation_groups_view_sql,
    solvation_libraries_view_sql,
    solute_libraries_view_sql,
    solvent_libraries_view_sql,
    label_pairs_view_sql,
)

from .triggers import (
    check_short_desc,
    delete_empty_desc,
    validate_solvent_parameters,
    validate_data_count,
)

__all__ = [
    # Schema classes
    'SCHEMA_BASE',
    'Groups',
    'GroupsTree', 
    'SolvationLibraries',
    'SoluteLibrary',
    'SolventLibrary',
    'SoluteData',
    'SolventData',
    'DataCountGAV',
    'DataCountSolvent',
    
    # Views
    'solvation_groups_view_sql',
    'solvation_libraries_view_sql',
    'solute_libraries_view_sql',
    'solvent_libraries_view_sql',
    'label_pairs_view_sql',
    
    # Triggers
    'check_short_desc',
    'delete_empty_desc',
    'validate_solvent_parameters',
    'validate_data_count',
]

__version__ = "1.0.0"
