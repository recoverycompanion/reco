import pandas as pd
import numpy as np
import os

new_directory = r"../data/raw/mimic/"  # Update the relative path accordingly
os.chdir(new_directory)

list_dir = os.listdir()

starting_csv_file_name = 'mimic_ed_hf_240609_1741.csv'

ccs_to_omit=['Transfer', 'Abnormal labs', 'Meds refill']

df = pd.read_csv(starting_csv_file_name)

def clean_chief_complaint(s):
    if '"' in s:
        if s[0] == '"':
            s = s[1:]
        if s[-1] == '"':
            s = s[:-1]
    for cc in ccs_to_omit:
        if cc in s:
            if ", " + cc in s:
                s = s.replace(', ' + cc, '')
            if cc + ", " in s:
                s = s.replace(cc + ', ', '')
            if cc in s:
                s = s.replace(cc, '')
    if s == '':
        s = "REMOVE_ROW"

    return s

df['chiefcomplaint'] = df['chiefcomplaint'].apply(clean_chief_complaint)

filtered_df = df[df['chiefcomplaint'] != 'REMOVE_ROW']

#print(f"Removed {len(df) - len(filtered_df)} rows")

filtered_df.to_csv('mimic_ed_hf_cleaned_06_30_2024.csv')
                
                