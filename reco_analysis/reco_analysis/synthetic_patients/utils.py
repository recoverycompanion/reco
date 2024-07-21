"""
This script contains utility functions for cleaning the chief complaint field in the MIMIC dataset, calculating demographic distributions for synthetic patient generation, generating the top 100 last names for different racial groups, and collecting a list of patients to exclude from synthetic generation.
"""

import pandas as pd
import numpy as np
import json

INPUT_FILE_PATH = '../data/raw/mimic/mimic_ed_hf_240609_1741.csv'
CLEANED_FILE_PATH = '../data/processed/mimic_ed_hf_240609_1741_cleaned.csv'

def clean_chief_complaint(in_file_path: str, out_file_path: str, ccs_to_omit: list = ['Transfer', 'Abnormal labs', 'Meds refill']):
    """
    Clean the chief complaint field in the csv file.

    Args:
        in_file_path: Path to the csv file.
        out_file_path: Path to the output csv file.
        ccs_to_omit: List of chief complaints to omit.
    """
    def _clean_chief_complaint_string(s):
        if '"' in s:
            s = s.replace('"', '')
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
    
    df = pd.read_csv(in_file_path)
    df['chiefcomplaint'] = df['chiefcomplaint'].apply(_clean_chief_complaint_string)
    df = df[df['chiefcomplaint'] != 'REMOVE_ROW']
    df.to_csv(out_file_path, index=False)
    return df

def calculate_demographics(csv_file_path: str, records_to_generate: int):
    """
    Calculates demographic distributions for synthetic patient generation.

    Args:
        csv_file_path (str): The path to the input CSV file.
        records_to_generate (int): The number of synthetic patients to generate.

    Returns:
        dict: A dictionary with the number of patients to generate for each race.
    """
    df = pd.read_csv(csv_file_path)
    
    def _get_value_percentages(df, column_name):
        total_rows = len(df)
        value_counts = df[column_name].value_counts()
        percentages = (value_counts / total_rows)
        result_df = pd.DataFrame({
            'Race': value_counts.index,
            'Count': value_counts.values,
            'MIMIC Pct': percentages.values,
        })
        return result_df

    column_name = 'race'
    result = _get_value_percentages(df, column_name)

    census_percentages = [60.1, 12.3, 19.4, 1.9, 5.6, 0.8]
    result['Census Percentages'] = census_percentages

    incidence_rates = [2.4, 4.6, 3.5, 1, 1, 1]
    result['Incidence Rates'] = incidence_rates
    result['Incidence Step 1'] = result['Census Percentages'] * result['Incidence Rates']
    result['Incidence Pct'] = result['Incidence Step 1'] / sum(result['Incidence Step 1'])

    result['Incidence Adj Pct'] = result.apply(
        lambda row: row['MIMIC Pct'] if (row['MIMIC Pct'] > row['Incidence Pct'] and row['Incidence Pct'] < 0.1) else row['Incidence Pct'], axis=1
    )
    total_combined_pct = result['Incidence Adj Pct'].sum()
    result['Incidence Adj Pct'] = result['Incidence Adj Pct'] / total_combined_pct

    result['Num_Patients_Calc'] = result['Incidence Adj Pct'] * records_to_generate

    num_patients_values = result['Num_Patients_Calc'].tolist()
    patients_adj = [int(round(num, 0)) if num >= 1 else int(1) for num in num_patients_values]

    sum_patients = sum(patients_adj)
    extra_patients = sum_patients - records_to_generate

    if extra_patients < 0:
        for i in range(abs(extra_patients)):
            random_number = np.random.choice(len(patients_adj))
            patients_adj[random_number] += 1

    if extra_patients > 0:
        for i in range(extra_patients):
            patients_adj[patients_adj.index(max(patients_adj))] -= 1

    result['Num_Patients_Adj'] = patients_adj

    columns_to_keep = ['Race', 'MIMIC Pct', 'Incidence Adj Pct', 'Num_Patients_Calc', 'Num_Patients_Adj']
    sub_result = result[columns_to_keep].copy()

    race = sub_result['Race'].tolist()
    count = sub_result['Num_Patients_Adj'].tolist()
    result_dict = {k: v for k, v in zip(race, count)}

    return result_dict

def generate_top_last_names(csv_file_path: str = '../data/raw/names/last_raceNameProbs.csv', output_file_path: str = '../data/processed/names/top_100_last_names_by_value.csv'):
    """
    Generates the top 100 last names for different racial groups.

    Args:
        csv_file_path (str): The path to the input CSV file.
        output_file_path (str): The path to save the output CSV file with top last names.
    """
    df = pd.read_csv(csv_file_path)

    columns_to_process = ['whi', 'bla', 'his', 'asi', 'oth']
    top_100_by_column = {}

    for col in columns_to_process:
        sorted_df = df.sort_values(by=col, ascending=False)
        top_100_subset = sorted_df.head(100)[['name', col]]
        top_100_subset = top_100_subset[top_100_subset['name'] != 'ALL OTHER NAMES']
        top_100_by_column[col] = top_100_subset

    top_100_df = pd.concat(top_100_by_column.values())
    top_100_df.reset_index(drop=True, inplace=True)

    df_merged = top_100_df.groupby('name').agg(lambda x: x.first_valid_index()).reset_index()

    columns_to_normalize = ['whi', 'bla', 'his', 'asi', 'oth']
    for col in columns_to_normalize:
        total = df_merged[col].sum()
        df_merged[col] = df_merged[col] / total
        df_merged[col] = df_merged[col].fillna(0)

    df_merged.to_csv(output_file_path, index=False)

def get_patients_to_exclude(file_path: str):
    """
    Collects a list of patients to exclude from synthetic generation from a specified JSON file.

    Args:
        file_path (str): The path to the JSON file containing patient data to exclude.

    Returns:
        list: A list of patient IDs to exclude.
    """
    if file_path:
        with open(file_path, 'r') as f:
            read_t_file = json.load(f)

        patients_to_exclude = list(read_t_file.keys())

        return patients_to_exclude
    
    else:
        return []