#!/bin/bash

python scripts/fetch_latest_rmg_data.py

# Define the chemical property types
chemical_types=("kinetics" "solvation" "thermo" "statmech" "transport")

# Loop through each chemical property type
for type in "${chemical_types[@]}"; do
    echo "Building $type database..."
    cd "data/rmgdatabase/$type"

    # Remove existing database
    rm "${type}.db" || true

    # Build and validate the database
    python build.py
    python round_trip.py

    # Copy the built database to the db directory
    cp "${type}.db" "../../../db/${type}.db"

    # Return to the main directory
    cd ../../../
done

echo "All databases built successfully!"