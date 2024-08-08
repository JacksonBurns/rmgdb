import pandas as pd

statmech_df = pd.read_sql("SELECT * FROM statmech_libraries_view", "sqlite:///demo_v2.db")
print(statmech_df)
