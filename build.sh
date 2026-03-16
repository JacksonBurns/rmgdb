cd data/rmgdatabase/kinetics
rm kinetics.db || true
python build.py
python round_trip.py
cd ../solvation
rm solvation.db || true
python build.py
python round_trip.py
cd ../thermo
rm thermo.db || true
python build.py
python round_trip.py
cd ../statmech
rm statmech.db || true
python build.py
python round_trip.py
cd ../transport
rm transport.db || true
python build.py
python round_trip.py
cd ../../../
