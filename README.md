# rmgdb
The ReactionMechanismGenerator Database Standard and Database

# About
This repository contains:
 - a standard specification for databases containing chemical information of various types, referred to as the ReactionMechanismGenerator Database Standard, or rmgdb standard in the `rmgdb` directory.
 - the official RMG database of chemical information, which adheres to this format, in the `data` directory.

The goal is to eventually package both of these as separate tools - the former to enable others to create databases from scratch, and the latter to use the RMG database for their work or to extend it.
This could take the form of `rmgdatabase` being the base standard definition, and then the option `rmgdatabase[data]` package containing all of the actual numbers.

## Purpose
Storing chemical data is very amenable to the use of relational databases.
Many of the concepts such as required columns, input validation, and key relationships map directly to chemistry concepts like provenance tracking, formula validation, and structure/substructure comparisons, respectively.

The idea here is to provide one standard implementation of this as well as a useful demo example which is easily accessible.
The [current version of RMG-database](https://github.com/ReactionMechanismGenerator/RMG-database) is not easy to use - all of the data is stored in Python files as function calls (to classes which are not even _in_ that repository).
This was a convenient format at its inception, but is terse, difficult to validate, not scalable, and just generally not taking advantage of existing technologies.

## Inspiration
The [`SIMPLE-db`](https://github.com/SIMPLE-AstroDB/SIMPLE-db) project is a _fantastic_ example of open source data management.
This project achieves a lot of what we want here:
 - standard implementation of a format (in this case for astrological data)
 - readily version controlled JSON dumps of the database, which can be edited by users in plaintext
 - deployable version of the database using a 'real' database format
Thank you to [@kelle](https://github.com/kelle) for putting this project on our radar!

# Moving from RMG-database to rmgdb
To actually migrate, we will define the schema in this repository, spoof the RMG classes and execute the existing database files as RMG does to load them into a database, dump that into a better plaintext format.

Reimplementing the tree structure will be difficult, but there is of course lots of existing technology to do this - see: https://docs.sqlalchemy.org/en/20/orm/self_referential.html about SQL Adjacency list and this even more closely related example: https://docs.sqlalchemy.org/en/20/orm/join_conditions.html#self-referential-many-to-many.
Relevant blog post: https://www.kite.com/blog/python/sqlalchemy/
