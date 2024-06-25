import pandas as pd
import numpy as np
import os

records_to_generate = 20

print()
print(f"To generate {records_to_generate} patients\nConsider the following demographics:")

new_directory = r"../data/raw/mimic/"  # Update the relative path accordingly
os.chdir(new_directory)

list_dir = os.listdir()

csv_file_name = list_dir[1]

df = pd.read_csv(csv_file_name)

# Function to get values and corresponding percentages
def get_value_percentages(df, column_name):
    # Total number of rows
    total_rows = len(df)
    
    # Count of each value in the specified column
    value_counts = df[column_name].value_counts()
    
    # Calculate percentages
    percentages = (value_counts / total_rows)
    
    # Create a new DataFrame to store results
    result_df = pd.DataFrame({
        'Race': value_counts.index,
        'Count': value_counts.values,
        'MIMIC Pct': percentages.values,
    })
    
    return result_df

column_name = 'race'
result = get_value_percentages(df, column_name)

#chief_complaints = get_value_percentages(df, 'chiefcomplaint')
#print(chief_complaints)

### Incorporating U.S. demographics
# https://nces.ed.gov/pubs2010/2010015/tables/table_1a.asp

census_percentages = [60.1, 12.3, 19.4, 1.9, 5.6, 0.8]

result['Census Percentages'] = census_percentages

### Incorporating heart failure incidence by race/ethnicity from
#  https://www.sciencedirect.com/science/article/pii/S0735109721079018

incidence_rates = [2.4, 4.6, 3.5, 1, 1, 1]

result['Incidence Rates'] = incidence_rates
result['Incidence Step 1'] = result['Census Percentages'] * result['Incidence Rates']
result['Incidence Pct'] = result['Incidence Step 1'] / sum(result['Incidence Step 1'])

### Create combined percentage to better ensure representation of smaller demographic groups

result['Incidence Adj Pct'] = result.apply(lambda row: row['MIMIC Pct'] if (row['MIMIC Pct'] > row['Incidence Pct'] and row['Incidence Pct'] < 0.1) else row['Incidence Pct'], axis=1)

# Normalize Incidence column
total_combined_pct = result['Incidence Adj Pct'].sum()
result['Incidence Adj Pct'] = result['Incidence Adj Pct'] / total_combined_pct

result['Num_Patients_Calc'] = result['Incidence Adj Pct'] * records_to_generate

num_patients_values = result['Num_Patients_Calc'].tolist()

patients_adj = []

for num in num_patients_values:
    if num < 1:
        patients_adj.append(int(1))
    else:
        patients_adj.append(int(round(num, 0)))

sum_patients = sum(patients_adj)
extra_patients = sum_patients - records_to_generate

if extra_patients < 0:
    for i in range(extra_patients * -1):
        random_number = np.random.choice(6)
        print(random_number)
        patients_adj[random_number] += 1

if extra_patients > 0:
    for i in range(extra_patients):
        patients_adj[patients_adj.index(max(patients_adj))] -= 1

result['Num_Patients_Adj'] = patients_adj

columns_to_keep = ['Race', 'MIMIC Pct', 'Incidence Adj Pct', 'Num_Patients_Calc', 'Num_Patients_Adj']

sub_result = result[columns_to_keep].copy()

print()
print(sub_result)
print()

print("Results as a Dictionary")
race = sub_result['Race'].tolist()
count = sub_result['Num_Patients_Adj'].tolist()

result_dict = {k: v for k, v in zip(race, count)}

print(result_dict)
print()