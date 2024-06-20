import pandas as pd
import numpy as np
import os

new_directory = r"../data/raw/mimic/"  # Update the relative path accordingly
os.chdir(new_directory)

list_dir = os.listdir()

csv_file_name = list_dir[1]

df = pd.read_csv(csv_file_name)

null_report = {}
for column in df.columns:
    null_count = df[column].isnull().sum()
    null_report[column] = null_count

random_row_index = np.random.choice(df.index)
random_row = df.iloc[random_row_index]

### MIMIC DATA

gender = random_row['gender']
race = random_row['race']
age = random_row['age']

if pd.isna(random_row['marital_status']):
    marital_status = "Prefer not to say"
else:
    marital_status = random_row['marital_status']

icd_title = random_row['icd_title']
chiefcomplaint = random_row['chiefcomplaint']
vitals_temperature = random_row['vitals_temperature']
vitals_heartrate = int(random_row['vitals_heartrate'])
vitals_resprate = int(random_row['vitals_resprate'])
vitals_o2sat = random_row['vitals_o2sat']
vitals_sbp = int(random_row['vitals_sbp'])
vitals_dbp = int(random_row['vitals_dbp'])
vitals_pain = int(random_row['vitals_pain'])
vitals_rhythm = random_row['vitals_rhythm']
hosp_discharge_location = random_row['hosp_discharge_location']
all_meds = random_row['all_meds']

### PERSONALITY

patient_feelings = ['Normal', 'Anxious about your health', 'Grateful for your care team', 'Confused about your care plan', 'Somewhat hopeless about your condition', 'A little annoyed with the questions']

random_number = np.random.choice(20)
if random_number < 15:
    num = 0
else:
    num = random_number - 14

primary_patient_feeling = patient_feelings[num]

patient_prompt = f"You are a patient who has been discharged after a hospital stay for heart failure. You are reporting your symptoms for a routine check in with your doctor. When the doctor prompts 'Hi there' continue the roleplay. Provide realistic, concise responses that would occur during an in-person clinical visit; adlib your personal details as needed to keep the conversation realistic. Responses should not exceed two sentences. Feel free to include some 'um...' and 'ahs' for moments of thought. Do not relay all information provided intiially. See profile below for information.\n\nGender: {gender}\nAge: {age}\nMarital status: {marital_status}\nCurrent symptoms: {chiefcomplaint}. Note that if your current symptoms include 'dyspnea' report it colloquially as 'shortness of breath' or 'hard to breathe'\nCurrent emotional state: {primary_patient_feeling}. Note that your disposition can improved based on a positive interaction with your doctor.\n\n Current medications: {all_meds}. Note that you should report the meds only a few at a time before beginning a new sentence. Don't omit any meds in your response.\n\nWhen asked specifically about your vital signs, you may respond with the following information:\nTemperature: {vitals_temperature}\nHeart rate: {vitals_heartrate}. Note that the doctor may ask you this by asking you to count the number of beats for an interval of time.\nRespiratory rate: {vitals_resprate}. Note that the doctor may ask you this by asking you to count the number of breaths you take per minute.\nO2 saturation: {vitals_o2sat}. Note that the doctor may ask you this by asking you to get a reading from your pulse oximeter.\nBlood pressure: {vitals_sbp}/{vitals_dbp}\nPain: {vitals_pain}. Note that the doctor may ask you this by asking you to report your level of pain on a scale from 1 to 10."

print(patient_prompt)

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