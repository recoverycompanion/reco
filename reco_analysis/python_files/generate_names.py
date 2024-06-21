import pandas as pd
import numpy as np
import os

csv_file_last_names = 'last_raceNameProbs.csv'

df = pd.read_csv(csv_file_last_names)

#print(df.head(1))

# Dictionary to store top 100 names and their corresponding values
top_100_by_column = {}
columns_to_process = ['whi', 'bla', 'his', 'asi', 'oth']

# Iterate over each column
for col in columns_to_process:
    # Sort the DataFrame by the column 'col' in descending order
    sorted_df = df.sort_values(by=col, ascending=False)
    
    # Select the top 100 names and corresponding values from the sorted DataFrame
    top_100_subset = sorted_df.head(100)[['name', col]]

    # Remove rows with name "ALL OTHER NAMES"
    top_100_subset = top_100_subset[top_100_subset['name'] != 'ALL OTHER NAMES']
    
    # Store in the dictionary
    top_100_by_column[col] = top_100_subset

# Create a new DataFrame 'top_100_df' to store top 100 names and their values
top_100_df = pd.DataFrame()

# Iterate over the dictionary and concatenate the results into 'top_100_df'
for col, subset_df in top_100_by_column.items():
    top_100_df = pd.concat([top_100_df, subset_df])

# Reset index for the new DataFrame
top_100_df.reset_index(drop=True, inplace=True)

df_merged = top_100_df.groupby('name').agg(lambda x: x.first_valid_index()).reset_index()

columns_to_normalize = ['whi', 'bla', 'his', 'asi', 'oth']

for col in columns_to_normalize:
    total = df_merged[col].sum()
    df_merged[col] = df_merged[col] / total

    # Fill NaNs
    df_merged[col] = df_merged[col].fillna(0)

df_merged.to_csv('top_100_last_names_by_value.csv', index=False)