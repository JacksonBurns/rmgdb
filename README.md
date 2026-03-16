# rmgdb

This repository contains the ReactionMechanismGenerator Database standard (`standard/rmgdb`) and database generation code (`data/rmgdatabase`), which wraps the data from the original RMG-database format into a readily accessible SQLLite database.

## Usage

### Access Data

If you just want to _access_ the data, all you need is `pandas` (or `polars`, `narwhals`, etc.).
See the [demo](./demo.ipynb) for comprehensive instructions.
This uses the built version of the database in `demo_db`; to re-build it using other versions of RMG-database, see the next section on building and developing.

One can also access the database via the plaintext YAML-formatted files in the `data` subdirectories.
These can be readily inter-operated with standard software tools, including Python's YAML library.

### Build and Develop the Database

To build the actual binary database files and dump them into YAML, you need a Python environment (any modern version should work, original development used 3.14).
You should then navigate to `standard`, install `rmgdb` (i.e., `pip install -e .`), then navigate to `data` and install `rmgdatabase` (i.e., `pip install -e .`).
This will leave you with all the dependencies you need.

You can then run `. build.sh`, or take a look inside and see what the script is doing and run the steps individually.
Broadly, the way it works is:

 - `build.py` mocks the original RMG-database classes like `entry` to 'trick' the code into generating a database
 - `round_trip.py` dumps the built database back into a YAML (plaintext) format for easier version control, then rebuilds the binary database from these files (to ensure they are correct)

As you make changes, you can check that the database is correct:

 - to actually be able to run the Python source files from RMG-database, every single class and function has to be defined within `rmgdatabase`, so we are guaranteed that as long as the files can actually be _executed_, we are storing all of the information.
 - one should be able to run `build.py` and then `round_trip.py`, and then `round_trip.py` again without changing any of the generated `.yml` files (this process builds the binary database from the Python source files, then dumps them to YML, then rebuilds the binary from the dumped YML, i.e., if there is any change in tha YML that means that we don't have all the data in the binary format and that the YML is missing something that the Python source originally had).
 I have validated that this is the case for the (particularly complicated) kinetics database, but it should be checked for the others as well.

## About

This repository contains:

 - a standard specification for databases containing chemical information of various types packaged as `rmgdb`, referred to as the ReactionMechanismGenerator Database Standard, or rmgdb standard in the `rmgdb` directory.
 - the official RMG database of chemical information packaged as `rmgdatabase`, which adheres to the `rmgdb` format, in the `data` directory.

The idea here is to provide one standard implementation of this as well as a useful demo example which is easily accessible.
The [current version of RMG-database](https://github.com/ReactionMechanismGenerator/RMG-database) is not easy to use - all of the data is stored in Python files as function calls (to classes which are not even _in_ that repository).
This was a convenient format at its inception, but is terse, difficult to validate, not scalable, and just generally not taking advantage of existing technologies.


## Future Plans

There are four broad steps for developing this code:

 1. (completed) The 'Access' Phase: make all of the data in RMG-database more readily accessible via a simple relational database, only requiring `pandas`.
 This goes a long way to make the data in RMG-database FAIR, and enables us to easily extract the data for use in external machine learning, data mining, or other projects.
 2. (provisional) The 'Integration' Phase: make RMG-Py use this new `rmgdatabase` in place of its current use of RMG-database, which has promising speed and memory usage benefits.
 This stage would not _replace_ RMG-database as a code repository, and would instead be built on top of it (like, via Continuous Integration) on an ongoing basis.
 3. (unscheduled) The 'Replacement' Phase: actually _replace_ RMG-database with this repository, moving our default storage format to the YAML files contained herein.
 This would require re-implementing much of the tooling built around the historic version of RMG-database, which is unlikely.

## See Also

The [`SIMPLE-db`](https://github.com/SIMPLE-AstroDB/SIMPLE-db) project is a _fantastic_ example of open source data management.
This project achieves a lot of what we want here:

 - standard implementation of a format (in this case for astrological data)
 - readily version controlled JSON dumps of the database, which can be edited by users in plaintext
 - deployable version of the database using a 'real' database format

Thank you to [@kelle](https://github.com/kelle) for putting this project on our radar!
