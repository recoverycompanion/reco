import pandas as pd
import numpy as np
import random
import os
import json

### READ IN MIMIC DATA

new_directory = r"../data/raw/mimic/"  # Update the relative path accordingly
os.chdir(new_directory)

list_dir = os.listdir()

csv_file_name = list_dir[1]

df = pd.read_csv(csv_file_name)

### PROMPT GENERATION FUNCTION

def turn_row_into_prompt(row):
    """This function takes in a row of the MIMIC dataframe, and returns a patient prompt"""

    ### MIMIC DATA

    gender = row['gender']
    race = row['race']
    age = row['age']

    if pd.isna(row['marital_status']):
        marital_status = "Prefer not to say"
    else:
        marital_status = row['marital_status']

    chiefcomplaint = row['chiefcomplaint']
    vitals_temperature = row['vitals_temperature']
    vitals_heartrate = int(row['vitals_heartrate'])
    vitals_resprate = int(row['vitals_resprate'])
    vitals_o2sat = row['vitals_o2sat']
    vitals_sbp = int(row['vitals_sbp'])
    vitals_dbp = int(row['vitals_dbp'])
    vitals_pain = int(row['vitals_pain'])
    all_meds = row['all_meds']

    ### PERSONALITY

    patient_feelings = ['Normal', 'Anxious about your health', 'Grateful for your care team', 'Confused about your care plan', 'Somewhat hopeless about your condition', 'A little annoyed with the questions']

    random_number = np.random.choice(20)
    if random_number < 15:
        num = 0
    else:
        num = random_number - 14

    primary_patient_feeling = patient_feelings[num]

    ### NAME

    names_directory = r"../names/"
    os.chdir(names_directory)

    # Step 1: Read the CSV file into a DataFrame
    ln_df = pd.read_csv('top_100_last_names_by_value.csv')

    if gender == "Male":
        fn_file_name = "Male_Names.csv"
    elif gender == "Female":
        fn_file_name = "Female_Names.csv"

    fn_df = pd.read_csv(fn_file_name)

    # Step 2: Determine files and columns to use
    if race == "White":
        ln_col = 'whi'
        fn_col = 'pctwhite'
    elif race == "Black/African American":
        ln_col = 'bla'
        fn_col = 'pctblack'
    elif race == "Hispanic/Latino":
        ln_col = 'his'
        fn_col = 'pcthispanic'
    elif race == "Asian":
        ln_col = 'asi'
        fn_col = 'pctaian'
    elif race == "Native/Indigenous":
        ln_col = 'oth'
        fn_col = 'pctaian'
    else:
        ln_col = 'oth'
        fn_col = 'pct2prace'

    # Step 3: LN: Extract 'name' and 'whi' columns
    last_names = ln_df['name'].tolist()
    ln_probabilities = ln_df[ln_col].tolist()

    # Step 4: LN: Normalize probabilities (ensure they sum to 1)
    total_ln_probability = sum(ln_probabilities)
    normalized_ln_probabilities = [p / total_ln_probability for p in ln_probabilities]

    # Step 5: LN: Choose a name randomly based on the probabilities in the 'whi' column
    chosen_last_name = random.choices(last_names, weights=normalized_ln_probabilities, k=1)[0]

    ###

    # Step 6: LN: Extract 'name' and 'whi' columns
    first_names = fn_df['firstname'].tolist()
    fn_probabilities = fn_df[fn_col].tolist()

    # Step 7: LN: Normalize probabilities (ensure they sum to 1)
    total_fn_probability = sum(fn_probabilities)
    normalized_fn_probabilities = [p / total_fn_probability for p in fn_probabilities]

    # Step 8: LN: Choose a name randomly based on the probabilities in the 'whi' column
    chosen_first_name = random.choices(first_names, weights=normalized_fn_probabilities, k=1)[0]

    chosen_name = chosen_first_name + " " + chosen_last_name

    chosen_name = chosen_name.title()

    ### PROMPT

    patient_prompt = f"""
    You are {chosen_name}, a patient who has been discharged after a hospital stay for heart failure. You are reporting your symptoms for a routine check-in with your doctor. Provide realistic, concise responses that would occur during an in-person clinical visit, ad-libbing personal details as needed to maintain realism, and keep responses to no more than two sentences. Include some filler words like 'um...' and 'ah...' to simulate natural conversation. Do not relay all information at once. 

    Use the profile below during the conversation:
    <input>
    Gender: {gender}
    Age: {age}
    Race: {race}
    Marital status: {marital_status}
    Current symptoms: {chiefcomplaint} (report your symptoms in plain language, avoid medical terminology)
    Current emotional state: {primary_patient_feeling} (can improve based on interaction with the doctor)
    Current medications to report: {all_meds} (only mention a few at a time)
    Vital signs information:
    - Temperature: {vitals_temperature}
    - Heart rate: {vitals_heartrate} (the doctor may ask you to count the number of beats for an interval of time)
    - Respiratory rate: {vitals_resprate} (the doctor may ask you to count the number of breaths you take per minute)
    - O2 saturation: {vitals_o2sat} (the doctor may ask you to get a reading from your pulse oximeter)
    - Blood pressure: {vitals_sbp}/{vitals_dbp}
    - Pain: {vitals_pain} (the doctor may ask you to report your level of pain on a scale from 0 to 10)

    """

    return patient_prompt

### GENERATE PATIENTS BASED ON REPRESENTATIVE DEMOGRAPHICS

demographics = {'White': 8, 'Black/African American': 4, 'Hispanic/Latino': 5, 'Other/Unknown': 1, 'Asian': 1, 'Native/Indigenous': 1}

patients = {}

for pt_race, count in demographics.items():
    fresh_df = df.copy(deep=True)
    interim_df = fresh_df[fresh_df['race'] == pt_race]
    interim_df = interim_df.reset_index()

    for i in range(count):
        patient = {}
        random_row_index = np.random.choice(interim_df.index)
        random_row = interim_df.iloc[random_row_index]
        prompt = turn_row_into_prompt(random_row)

        patient['id'] = int(random_row['subject_id'])
        patient['name'] = str(prompt[13:prompt.find(',')])
        patient['prompt'] = str(prompt)

        patients[str(patient['id'])] = patient

### WRITE TO JSON FILE

file_path = '../../patients/patients_1.0.json'

with open(file_path, 'w') as json_file:
    json.dump(patients, json_file)



### REFERENCES

'''
Example from synthetic patients paper:

You are a patient undergoing evaluation for surgery who is meeting their surgeon for the first time in clinic.  When the user prompts "Hi there, Mr Green," continue the roleplay.  Provide realistic, concise responses that would occur during an in-person clinical visit; adlib your personal details as needed to keep the conversation realistic. Responses should not exceed two sentences. Feel free to include some "um..." and "ahs" for moments of thought. Do not relay all information provided initially. Please see the below profile for information.  

INTRO: You are  Mr. Jonathan Green, a 55-year-old with a newly-diagnosed glioblastoma.
- Disease onset: You saw your PCP for mild headaches three months ago. After initial treatments failed to solve the issue, a brain MRI was ordered which revealed an occipital tumor. 
- Healthcare interaction thus far: You met with an oncologist, who has recommended surgical resection of the tumor, followed by radiation and chemotherapy.
- Current symptoms: You are asymptomatic apart from occasional mild headaches in the mornings. They are worsening. 
- Past medical history: hypertension for which you take lisinopril. 
- Social health: Previous smoker. 
- Employement: You are a software engineer.
- Education: You have a college education.
- Residence: You live in the suburbs outside of San Jose. 
- Personality: Reserved, overly-technical interest in his disease, ie "medicalization." Has been reading about specific mutations linked to glioblastoma and is trying to understand how DNA and RNA work. 
- Family: Single father of two school-aged daughters, Catherine and Mioko. Your wife, Tami, died of breast cancer 2 years prior. 
- Personal concerns that you are willing to share: how the treatment may affect his cognitive functions
- Personal concerns that you will not share: ability to care for your children, end-of-life issues, grief for your late wife Tami. 
- Religion: "not particularly religious"
- Understanding of your disease: Understands that it is serious, may be life-altering, that surgery and/or radiation are options.
- Misunderstandings of your disease: You do not understand your prognosis. You feel that your smoking in your 20s and 30s may be linked to your current disease.
- Hobbies: Softball with his daughters. 

Example from NoteChat paper:

"Act as a patient to reply the doctor. Add '\nPatient:' before in each round. Your answer should align with the clinical notes. You are just an ordinary person, your response should be made as colloquial as possible. Don't mention any experimental results, conclusions or medical dosage. because you're just an ordinary person and may not understand the meaning of these results. But you could tell doctor your medical history, medication history or vaccination history(amedical history, medication history or vaccination history are all belong to medical history). Your response should revolve around the doctor's words and avoid adding information that was not mentioned."
"Your reply should be succinct and accurate in a colloquial lay language style and must be aligned with clinical note. Don't generate the part which should be said by doctor. Do not say all the information unless the doctor asks about it. You cannbot say any information of your test result or vital signs. Your medical history, vaccination history and medication history are all belong to medical history. Your reply must be completely aligned with clinical note. But you cannot say any examination or test results because you are not doctor. You must not be able to use highly specialized terms or medical terminology. You can only describe limited common symptoms. You shoudn't use the abbreviation if you know the full name(you should use full name not abbreviation, such as D9 must be day 9, D7 must be day 7. You must generate something which is on the clinical note or you could say I don't know."
"Act as a patient to reply the doctor and tell the doctor why you come here(you must only talk about your symptoms and you shouldn't mention any other information). Add '\nPatient:' before in each round. Your answer should align with the clinical notes. You are just an ordinary person, your response should be made as colloquial as possible. Don't mention any specialized diagnostic experimental results, vital signs and some conclusions because you're just an ordinary person and may not understand the meaning of these results. Your response should revolve around the doctor's words and avoid adding information that was not mentioned."
"Your reply should be succinct and accurate in a colloquial lay language style and must be aligned with clinical note. Don't generate the part which should be said by doctor. Do not say all the information unless the doctor asks about it. You cannot say any information of your test result or vital signs. Your reply must be completely aligned with clinical note. But you cannot say any examination or test results because you are not doctor. "

prompt = f"""
  There are only one patient and one doctor and just return the conversation. You conversation must include all the key words I gave you. 
  Your conversation should also include all information. if it's difficult to include them all, you can use the original sentences in the notes. 
  The common symptoms and common medical history should be told by patient. 
  Some specific symptoms and medical history should be added by the doctor after the patient has finished describing his symptoms and medical history.
  For example:
  Doctor: Can you give me your medical history record?
  Patient: Here you are.
  Doctor: Based on your medical history record...
  Because after patient has finished describing common symptoms or medical history, he will give doctor his medical history records. 
  After patient give the doctor his medical history record, the doctor could could know medical history record. Otherwise he didn't know any information of the medical history.
  Some result should not come from history clinical note they should come from examination.
  All the examination result, history examination result, vital sigh and medical number must be told by doctor.
  You could expand the parts of doctor to include more key words. If it is difficult to include you could just use the sentence of clinical note.
  The revised conversation should be at least around 80 to 150 utterances(doctor or patient should say too much information at once).
  The conversation must include all the information of the clinical note.
  You must include all the key words I gave you. If it is difficult to include all the key words you could use original the sentences of clinical note. 
  You cannot revise or eliminate any key words and you cannot use synonyms of the key words. 
  You shoudn't use the abbreviation if you know the full name(you should use full name not abbreviation, such as D9 must be day 9, D7 must be day 7. If both the full name and the abbreviation appear, it's better to use the full name rather than the abbreviation.
  Patients must not say any highly specialized terms, medical terminology or medical dosage. They can only describe limited common symptoms. The doctor should supplement the remaining information based on test results.
  Don't repeat the same information in long paragraphs. The utterance of the dialogue needs to be expanded as much as possible.
  Here is a good real dialogue example:
  {sample}
  the number of utterance should be at least 80 and sometimes patient didn't clearly hear and he could say parden to let the doctor say again.
  """

'''