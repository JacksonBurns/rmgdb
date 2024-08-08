import pandas as pd

statmech_df = pd.read_sql("SELECT * FROM statmech_libraries_view", "sqlite:///demo.db")
print(statmech_df)
