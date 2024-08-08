from sqlite3 import connect
import pandas as pd

conn = connect("demo.db")
statmech_df = pd.read_sql("SELECT * FROM statmech_libraries_view", conn)
print(statmech_df)
