# Synthetic Patients

This folder contains scripts for generating synthetic patient data based on the MIMIC-ED dataset. The scripts include utility functions for data cleaning and demographic calculations, as well as the main script for creating synthetic patients.

## Contents

- **data_prep.py**: Utility functions for data processing.
- **create_patients.py**: Main script for generating synthetic patients.

## Scripts

### data_prep.py

Utility functions for data cleaning, demographic calculations, name generation, and patient exclusion.

#### Functions

- **clean_chief_complaint(in_file_path, out_file_path)**: Cleans the chief complaint field in the CSV file.
- **calculate_demographics(csv_file_path, records_to_generate)**: Calculates demographic distributions for synthetic patient generation.
- **generate_top_last_names(csv_file_path, output_file_path)**: Generates the top 100 last names for different racial groups.
- **get_patients_to_exclude(file_path)**: Collects a list of patients to exclude from synthetic generation from a specified JSON file.

### create_patients.py

Main script for creating synthetic patients using demographic data and a list of names.

#### Functions

- **create_prompt_template()**: Converts the prompt text into a LangChain PromptTemplate object
- **turn_row_into_prompt(row, last_names_file, male_first_names_file, female_first_names_file, additional_text)**: Converts a row of the MIMIC dataframe into a patient prompt.
- **create_synthetic_patients(n, cleaned_mimic_file_path, male_first_names_file, female_first_names_file, last_names_file, patients_to_exclude, additional_text)**: Creates synthetic patients using demographic data and a list of names.

## Usage

1. **Clean Chief Complaint Data**
    ```python
    from reco_analysis.synthetic_patients.data_prep import clean_chief_complaint
    clean_chief_complaint(RAW_MIMIC_FILE, CLEANED_MIMIC_FILE)
    ```

2. **Generate Top Last Names**
    ```python
    from reco_analysis.synthetic_patients.data_prep import generate_top_last_names
    generate_top_last_names(LAST_NAMES_FILE, PROCESSED_LAST_NAMES_FILE)
    ```

3. **Get Patients to Exclude**
    ```python
    from reco_analysis.synthetic_patients.data_prep import get_patients_to_exclude
    patients_to_exclude = get_patients_to_exclude(PATIENTS_EXCLUDE_FILE)
    ```

4. **Create Synthetic Patients**
    ```python
    from reco_analysis.synthetic_patients.create_patients import create_synthetic_patients
    synthetic_patients = create_synthetic_patients(20, CLEANED_MIMIC_FILE, MALE_FIRST_NAMES_FILE, FEMALE_FIRST_NAMES_FILE, PROCESSED_LAST_NAMES_FILE, patients_to_exclude)
    ```

5. **Save Synthetic Patients**
    ```python
    from reco_analysis.synthetic_patients.create_patients import export_synthetic_patients
    export_synthetic_patients(synthetic_patients, './data/patients/transcripts.json')
    ```

## File Paths

Adjust file paths in the scripts as needed:
- `RAW_MIMIC_FILE`
- `CLEANED_MIMIC_FILE`
- `LAST_NAMES_FILE`
- `PROCESSED_LAST_NAMES_FILE`
- `MALE_FIRST_NAMES_FILE`
- `FEMALE_FIRST_NAMES_FILE`
- `PATIENTS_EXCLUDE_FILE`
- `OUTPUT_PATIENTS_FILE`