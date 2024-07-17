import pandas as pd
import numpy as np
import random
import os
import json
from langchain.prompts import PromptTemplate
from reco_analysis.synthetic_patients.utils import clean_chief_complaint, calculate_demographics, generate_top_last_names, get_patients_to_exclude

# Define global variables for file paths
RAW_MIMIC_FILE = '../data/raw/mimic/mimic_ed_hf_240609_1741.csv'
CLEANED_MIMIC_FILE = '../data/processed/mimic/mimic_ed_hf_240609_1741_cleaned.csv'
LAST_NAMES_FILE = '../data/raw/names/last_raceNameProbs.csv'
PROCESSED_LAST_NAMES_FILE = '../data/processed/names/top_100_last_names_by_value.csv'
MALE_FIRST_NAMES_FILE = '../data/raw/names/Male_Names.csv'
FEMALE_FIRST_NAMES_FILE = '../data/raw/names/Female_Names.csv'
PATIENTS_EXCLUDE_FILE = ''
OUTPUT_PATIENTS_FILE = '../data/patients/patients_2.0_test.json'

# Define the prompt text template
PROMPT_TEXT = """
You are {name}, a patient who has been discharged after a hospital stay for heart failure. You are reporting your symptoms for a routine check-in with your doctor. Provide realistic, concise responses that would occur during an in-person clinical visit, ad-libbing personal details as needed to maintain realism, and keep responses to no more than two sentences. Include some filler words like 'um...' and 'ah...' to simulate natural conversation. Do not relay all information at once.

Use the profile below during the conversation:
<input>
Gender: {gender}
Age: {age}
Race: {race}
Marital status: {marital_status}
Current symptoms: {chiefcomplaint}
Current emotional state: {primary_patient_feeling}
Current medications to report: {all_meds}
Vital signs information:
- Temperature: {vitals_temperature}
- Heart rate: {vitals_heartrate}
- Respiratory rate: {vitals_resprate}
- O2 saturation: {vitals_o2sat}
- Blood pressure: {vitals_sbp}/{vitals_dbp}
- Weight: {weight} pounds
- Pain: {vitals_pain}
"""

def create_prompt_template(prompt_text=PROMPT_TEXT):
    """
    Creates a prompt template for the language model using LangChain.

    Args:
        prompt_text (str): The text of the prompt template.

    Returns:
        PromptTemplate: A LangChain PromptTemplate object.
    """
    return PromptTemplate(
        input_variables=["name", "gender", "age", "race", "marital_status", "chiefcomplaint", "primary_patient_feeling", "all_meds", "vitals_temperature", "vitals_heartrate", "vitals_resprate", "vitals_o2sat", "vitals_sbp", "vitals_dbp", "weight", "vitals_pain"],
        template=prompt_text,
    )

def turn_row_into_prompt(row, last_names_file, male_first_names_file, female_first_names_file, prompt_text=PROMPT_TEXT):
    """
    Converts a row of the MIMIC dataframe into a patient prompt.

    Args:
        row (pd.Series): A row of the MIMIC dataframe.
        last_names_file (str): Path to the CSV file containing last names by race.
        male_first_names_file (str): Path to the CSV file containing first names for males.
        female_first_names_file (str): Path to the CSV file containing first names for females.

    Returns:
        str: A patient prompt.
    """
    def _get_patient_feeling():
        patient_feelings = [
            'Normal', 'Anxious about your health', 'Grateful for your care team',
            'Confused about your care plan', 'Somewhat hopeless about your condition',
            'A little annoyed with the questions'
        ]
        random_number = np.random.choice(20)
        return patient_feelings[0] if random_number < 15 else patient_feelings[random_number - 14]

    def _get_last_name_column(race):
        last_name_map = {
            'White': 'whi',
            'Black/African American': 'bla',
            'Hispanic/Latino': 'his',
            'Asian': 'asi',
            'Native/Indigenous': 'oth'
        }
        return last_name_map.get(race, 'oth')

    def _get_first_name_column(race):
        first_name_map = {
            'White': 'pctwhite',
            'Black/African American': 'pctblack',
            'Hispanic/Latino': 'pcthispanic',
            'Asian': 'pctaian',
            'Native/Indigenous': 'pctaian'
        }
        return first_name_map.get(race, 'pct2prace')

    def _choose_name(gender, race):
        last_names_df = pd.read_csv(last_names_file)
        first_names_df = pd.read_csv(male_first_names_file if gender == "Male" else female_first_names_file)
        
        last_name_col = _get_last_name_column(race)
        first_name_col = _get_first_name_column(race)

        last_names = last_names_df['name'].tolist()
        last_name_prob = last_names_df[last_name_col].tolist()
        chosen_last_name = random.choices(last_names, weights=last_name_prob, k=1)[0]

        first_names = first_names_df['firstname'].tolist()
        first_name_prob = first_names_df[first_name_col].tolist()
        chosen_first_name = random.choices(first_names, weights=first_name_prob, k=1)[0]

        return f"{chosen_first_name.title()} {chosen_last_name.title()}"

    gender = row['gender']
    race = row['race']
    age = row['age']
    marital_status = "Prefer not to say" if pd.isna(row['marital_status']) else row['marital_status']
    chiefcomplaint = row['chiefcomplaint']
    weight = int(row['weight_lbs'])
    vitals_temperature = row['vitals_temperature']
    vitals_heartrate = int(row['vitals_heartrate'])
    vitals_resprate = int(row['vitals_resprate'])
    vitals_o2sat = row['vitals_o2sat']
    vitals_sbp = int(row['vitals_sbp'])
    vitals_dbp = int(row['vitals_dbp'])
    vitals_pain = int(row['vitals_pain'])
    all_meds = row['all_meds']

    primary_patient_feeling = _get_patient_feeling()
    chosen_name = _choose_name(gender, race)

    prompt_template = create_prompt_template(prompt_text)
    patient_prompt = prompt_template.format(
        name=chosen_name,
        gender=gender,
        age=age,
        race=race,
        marital_status=marital_status,
        chiefcomplaint=chiefcomplaint,
        primary_patient_feeling=primary_patient_feeling,
        all_meds=all_meds,
        vitals_temperature=vitals_temperature,
        vitals_heartrate=vitals_heartrate,
        vitals_resprate=vitals_resprate,
        vitals_o2sat=vitals_o2sat,
        vitals_sbp=vitals_sbp,
        vitals_dbp=vitals_dbp,
        weight=weight,
        vitals_pain=vitals_pain,
    )

    return patient_prompt

def create_patients(n,
                    cleaned_mimic_file_path=CLEANED_MIMIC_FILE,
                    male_first_names_file=MALE_FIRST_NAMES_FILE,
                    female_first_names_file=FEMALE_FIRST_NAMES_FILE,
                    last_names_file=PROCESSED_LAST_NAMES_FILE,
                    patients_to_exclude=[],
                    prompt_text=PROMPT_TEXT):
    """
    Creates synthetic patients using demographic data and a list of names.

    Args:
        df (pd.DataFrame): The DataFrame containing the MIMIC-ED dataset.
        n (int): The number of synthetic patients to generate.
        cleaned_mimic_file_path (str): The path to the cleaned MIMIC-ED dataset.
        male_first_names_file (str): The path to the CSV file containing first names for males.
        female_first_names_file (str): The path to the CSV file containing first names for females.
        last_names_file (str): The path to the CSV file containing last names by race.
        patients_to_exclude (list): A list of patient IDs to exclude.

    Returns:
        dict: A dictionary of synthetic patients.
    """
    df = pd.read_csv(cleaned_mimic_file_path)

    patients = {}
    selected_patient_ids = set(patients_to_exclude)

    demographics = calculate_demographics(cleaned_mimic_file_path, n)

    for pt_race, count in demographics.items():
        interim_df = df[df['race'] == pt_race].reset_index(drop=True)
        filtered_df = interim_df[~interim_df['subject_id'].isin(selected_patient_ids)]
        list_to_choose_from = filtered_df['stay_id'].tolist()

        for _ in range(count):
            if not list_to_choose_from:
                raise ValueError(f"Ran out of patients to choose from this demographic group: {pt_race}")

            random_stay_id = random.choice(list_to_choose_from)
            list_to_choose_from.remove(random_stay_id)
            random_row = filtered_df[filtered_df['stay_id'] == random_stay_id].iloc[0]

            patient_prompt = turn_row_into_prompt(random_row, last_names_file, male_first_names_file, female_first_names_file, prompt_text)

            start_index = patient_prompt.find("You are ") + len("You are ")
            end_index = patient_prompt.find(",", start_index)
            full_name = patient_prompt[start_index:end_index]

            patient = {
                'id': int(random_row['subject_id']),
                'name': full_name,
                'prompt': patient_prompt,
            }

            patients[str(patient['id'])] = patient
            selected_patient_ids.add(random_row['subject_id'])

    return patients

def export_synthetic_patients(patients, output_file_path=OUTPUT_PATIENTS_FILE):
    """
    Exports the synthetic patients to a JSON file.

    Args:
        patients (dict): A dictionary of synthetic patients.
        output_file_path (str): The path to the output JSON file.
    """
    with open(output_file_path, 'w') as json_file:
        json.dump(patients, json_file)

if __name__ == "__main__":    
    # Step 1: Clean Chief Complaint Data
    clean_chief_complaint(RAW_MIMIC_FILE, CLEANED_MIMIC_FILE)

    # Step 2: Generate Top Last Names
    generate_top_last_names(LAST_NAMES_FILE, PROCESSED_LAST_NAMES_FILE)

    # Step 3: Get Patients to Exclude
    patients_to_exclude = get_patients_to_exclude(PATIENTS_EXCLUDE_FILE)

    # Step 4: Create Synthetic Patients
    synthetic_patients = create_patients(20, CLEANED_MIMIC_FILE, MALE_FIRST_NAMES_FILE, FEMALE_FIRST_NAMES_FILE, PROCESSED_LAST_NAMES_FILE, patients_to_exclude)

    # Step 5: Save Synthetic Patients
    export_synthetic_patients(synthetic_patients, OUTPUT_PATIENTS_FILE)