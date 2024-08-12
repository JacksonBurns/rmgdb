# rmgdb
The ReactionMechanismGenerator Database Standard and Database

# About
This repository contains:
 - a standard specification for databases containing chemical information of various types packaged as `rmgdb`, referred to as the ReactionMechanismGenerator Database Standard, or rmgdb standard in the `rmgdb` directory.
 - the official RMG database of chemical information packaged as `rmgdatabase`, which adheres to the `rmgdb` format, in the `data` directory.

## Purpose
Storing chemical data is very amenable to the use of relational databases.
Many of the concepts such as required columns, input validation, and key relationships map directly to chemistry concepts like provenance tracking, formula validation, and structure/substructure comparisons, respectively.

The idea here is to provide one standard implementation of this as well as a useful demo example which is easily accessible.
The [current version of RMG-database](https://github.com/ReactionMechanismGenerator/RMG-database) is not easy to use - all of the data is stored in Python files as function calls (to classes which are not even _in_ that repository).
This was a convenient format at its inception, but is terse, difficult to validate, not scalable, and just generally not taking advantage of existing technologies.

## Why
 1. Reusability - can actually interrogate RMG-database now, and you can update it _waaaaaaay_ more easily. Example of the former would be withdrawing SMILES and a property and passing to Chemprop.
 2. Scalabilty and Speed - doing the tree searching and lookup operations in SQL is much faster than the current approach
 3. Because We Can - existing approach relies on `exec` is not debuggable and should be replaced, all of the functions we need can easily be done in SQL.
 4. Safety - current version uses bad coding practice.

# Moving from RMG-database to rmgdb
## Phase 1 - Building the Database from Existing `.py` Files
The first step in this process is to build the database from the `.py` files directly by spoofing the functions and classes that they are trying to use to instead create rows in tables.

This requires defining a schema for the database, in which each class gets its own table, and then writing wrapper functions that accept the same arguments as the `.py` files are using and munge them to work for the database calls.

See `statmech` for a working example of this principle.

## Phase 2 - Shift to a new Plaintext Format
The `statmech` directory demonstrates how the database can be directly loaded into Python objects and then dumped into a human-editable YAML file for easy editing and adding of data.

At the end of this phase, when all of the data has been moved into the new plaintext format, the `.py` files can be deleted completely.

## Phase 3 - Re-implement Higher Level Functions
Implement some views in the database(s) and/or pure Python functions in a wrapper class that support loading the entire database, finding ancestors and descendants, navigating the tree, and loading actual RMG-Py objects (maybe).
To actually navigate the tree including subgraph-isomorphism comparisons, we should cache the calls of adjacency list -> molecule, which will make the database act like we have the whole set of molecules in memory.

## Phase 4 - Integrate with RMG-Py
This will be the first step where we actually _directly_ interact with RMG source code.

First, we should pass the RMG-Py unit tests.
This will require adding some new functions and maybe even modifying the schema somewhat, but since the core structure of this format is just a data holder, this should not happen a lot.

Next will be getting `rmgdatabase` to actually work in RMG-Py, replacing some of the functions that RMG-Py uses with equivalents over here (or over there).

# Inspiration
The [`SIMPLE-db`](https://github.com/SIMPLE-AstroDB/SIMPLE-db) project is a _fantastic_ example of open source data management.
This project achieves a lot of what we want here:
 - standard implementation of a format (in this case for astrological data)
 - readily version controlled JSON dumps of the database, which can be edited by users in plaintext
 - deployable version of the database using a 'real' database format
Thank you to [@kelle](https://github.com/kelle) for putting this project on our radar!
