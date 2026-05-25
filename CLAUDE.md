# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains the ReactionMechanismGenerator Database standard (`standard/rmgdb`) and database generation code (`data/rmgdatabase`), which wraps the data from the original RMG-database format into a readily accessible SQLLite database.

The project provides:
- A standard specification for databases containing chemical information (rmgdb package)
- The official RMG database of chemical information packaged as rmgdatabase, which adheres to the rmgdb format
- A conversion process that transforms the original RMG-database format into SQLLite databases with YAML dumps for version control

## Code Architecture

### Standard Package (`standard/rmgdb`)
- Contains the database schema definitions using SQLAlchemy
- Organized by chemical property types:
  - kinetics (reaction kinetics data)
  - thermo (thermodynamic data)
  - solvation (solvation data)
  - statmech (statistical mechanics data)
  - transport (transport properties data)
- Each module contains schema definitions and views for database tables

### Data Package (`data/rmgdatabase`)
- Contains the database generation code that builds the actual databases
- Each chemical property type has its own directory (kinetics, thermo, solvation, etc.)
- Uses build.py and round_trip.py scripts to generate and validate databases
- The build.py script mocks original RMG-database classes to generate databases
- The round_trip.py script dumps databases to YAML and rebuilds them to validate data integrity

## Key Commands

### Build and Develop the Database
To build the actual binary database files and dump them into YAML:
1. Navigate to `standard` and install `rmgdb`: `pip install -e .`
2. Navigate to `data` and install `rmgdatabase`: `pip install -e .`
3. Run `. build.sh` or execute the steps manually:
   - `build.py` mocks the original RMG-database classes to generate a database
   - `round_trip.py` dumps the built database back into YAML format, then rebuilds the binary database from these files

### Testing
The database build process validates data integrity by:
- Building the binary database from Python source files
- Dumping them to YAML
- Rebuilding the binary from the dumped YAML
- Ensuring no changes in the generated YAML files

## Development Workflow

1. Make changes to the data package (`data/rmgdatabase`)
2. Run the build process to regenerate the databases
3. Validate that the round_trip process produces no changes to YAML files
4. Test with the demo notebook to ensure functionality

## Key Files and Directories

- `build.sh` - Main build script that orchestrates database generation for all chemical property types
- `demo.ipynb` - Comprehensive demo showing how to access the database
- `standard/rmgdb/` - Standard database schema definitions
- `data/rmgdatabase/` - Database generation code for each chemical property type
- `demo_db/` - Pre-built demo databases for easy access