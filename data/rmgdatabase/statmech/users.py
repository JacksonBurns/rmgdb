import pandas as pd

QUERY = "SELECT * FROM statmech_libraries_view"

statmech_df = pd.read_sql(QUERY, "sqlite:///demo_v2.db")
print(statmech_df)


# import polars as pl
# import sqlite3

# with sqlite3.connect("demo_v2.db") as conn:
#     statmech_df = pl.read_database(QUERY, conn)

# print(statmech_df)
