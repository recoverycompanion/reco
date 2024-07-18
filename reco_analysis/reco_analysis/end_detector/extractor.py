"""
This script processes patient chat transcripts to identify and extract the first round of conversation
between a Doctor and a Patient. It utilizes LangChain and OpenAI's language model to determine where 
the first conversation ends based on specific dialogue cues.

Functions:
    - create_prompt_template: Generates a prompt template for the language model.
    - create_chain: Constructs a LangChain chain for the transcript extractor.
    - detect_first_conversation_end: Identifies the line number where the first conversation ends.
    - enumerate_transcript: Enumerates transcript lines for easier processing.
    - process_transcript: Processes a single transcript to extract the first round of conversation.
    - process_transcripts: Processes multiple transcripts to extract the first conversation for each.
    - load_transcripts: Loads transcripts from a JSON file.
    - save_transcripts: Saves processed transcripts to a JSON file.
"""
import json
import argparse
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv("../.env")
# Load environment variables
load_dotenv("../.env")

PROMPT_TEXT = """
You are an intelligent assistant tasked with identifying the line number where the first round of conversation ends in a transcript between a Doctor and a Patient.

You must only return a number.

Follow these steps:
1. **Identify the first conversation's end, if applicable:**
   - Look for a closing statement by the Doctor followed by a confirmation from the Patient. The last line of the first round should always be spoken by the Patient and end on a note indicating the conversation has reached a temporary conclusion.
   - Double-check that the last line of the first conversation does not contain a greeting or welcoming phrase typically used to start conversations.
2. **Identify the second conversation's start, if applicable:**
   - Usually indicated by the Doctor greeting the Patient again, e.g., "Hello [Patient name]". The first line of the second round is always spoken by the Doctor.
3. **If there is a first conversation end and second conversation start, double-check the transition:**
   - Confirm that the end of the first conversation appears immediately before the start of the second conversation.
4. **Output a number:**:
    - If there is no end to the first conversation, output 999.
    - If the first conversation ends, output the line number of the last line of the first conversation.

The transcript is provided below, surrounded by triple quotes:
'''
{transcript}
'''

Note: The example provided below applies only to cases where an end of the first conversation is identified.
**Example: Original Transcript:**
0: Doctor: Hello Kevin Morris, I'm here to check on how you're feeling today. Let's go over how you've been doing since your discharge.
1: Patient: Um... I've been feeling a bit tired lately, Doctor. And my legs are still swollen.
2: Doctor: I'm sorry to hear you're feeling tired, Kevin, and that your legs are still swollen. Let's address these symptoms further. Have you experienced any shortness of breath recently, especially when at rest, walking, or climbing stairs?
3: Patient: Um... I haven't had shortness of breath at rest, but I do feel a bit winded when I walk around the house. It's been a bit harder to move about.
4: Doctor: Thank you for sharing, Kevin. It's important to monitor these symptoms closely. Have you experienced sudden shortness of breath that wakes you up at night, known as paroxysmal nocturnal dyspnea?
5: Patient: No, Doctor, I haven't been waking up at night feeling short of breath. It's mostly during the day when I notice it more.
6: Doctor: Based on your responses, Kevin, it seems you're experiencing some shortness of breath with exertion during the day but not at night. Are you needing to prop yourself up with pillows to breathe comfortably while lying down?
7: Patient: No, Doctor, I don't need pillows to prop myself up at night. I usually sleep fine once I find a good position.
8: Doctor: Thank you for sharing that, Kevin. Have you noticed any swelling in your ankles or legs recently?
9: Patient: Yes, Doctor, my legs have been quite swollen, especially in the evenings. It's uncomfortable to move around when they're like that.
10: Doctor: Thank you for sharing that, Kevin. Are you experiencing a cough, especially at night?
11: Patient: No, Doctor, I haven't been coughing much at night. It's mostly during the day if I do.
12: Doctor: Thank you for clarifying, Kevin. Have you had any chest pain recently?
13: Patient: No, Doctor, I haven't had any chest pain recently. It's mostly been the tiredness and leg swelling that bother me.
14: Doctor: Thank you for letting me know, Kevin. Lastly, have you felt more tired than usual or experienced any sudden changes in your mental clarity?
15: Patient: No, Doctor, my mental clarity has been the same. Just feeling a bit more tired than usual.
16: Doctor: Based on your responses, Kevin, it seems like you're mainly experiencing tiredness and leg swelling. Could you please provide your latest vital signs, starting with your temperature?
17: Patient: My temperature is 97.4 degrees, Doctor.
18: Doctor: Thank you for the temperature reading, Kevin. What about your heart rate?
19: Patient: My heart rate is 74 beats per minute, Doctor.
20: Doctor: Thank you for sharing your heart rate, Kevin. Could you also provide me with your respiratory rate?
21: Patient: My respiratory rate is 18 breaths per minute, Doctor.
22: Doctor: Thank you for sharing your respiratory rate, Kevin. What is your oxygen saturation level?
23: Patient: My oxygen saturation level is 95.0%, Doctor.
24: Doctor: Thank you for sharing your oxygen saturation level, Kevin. Lastly, could you provide me with your blood pressure reading?
25: Patient: My blood pressure is 127/70, Doctor.
26: Doctor: Based on your responses, Kevin, your vital signs seem stable. Now, let's review the medications you are currently taking. Are you on any of the following medications: ACE inhibitors, Angiotensin II Receptor Blockers, ARNI, Beta-Blockers, Diuretics, Mineralocorticoid Receptor Antagonists, Hydralazine, Nitrate medications, Ivabradine, SGLT2 inhibitors, or GLP-1 agonists? Please confirm or list any other medications you are taking.
27: Patient: Yes, Doctor, I'm currently taking Furosemide and Spironolactone for my heart condition.
28: Doctor: Thank you for sharing your current medications, Kevin. Is there any other medication you are taking for your heart condition or any other health issue?
29: Patient: No, Doctor, those are the main ones for my heart. I also take some fish oil for general health.
30: Doctor: Based on our conversation, Kevin, it seems like you are mainly experiencing tiredness and leg swelling. Can you confirm if you are currently taking any ACE inhibitors, Angiotensin II Receptor Blockers, ARNI, Beta-Blockers, Diuretics, Mineralocorticoid Receptor Antagonists, Hydralazine, Nitrate medications, Ivabradine, SGLT2 inhibitors, or GLP-1 agonists for your heart condition? If not, please let me know if there are any other medications you are taking.
31: Patient: No, Doctor, I'm not on any of those medications you mentioned. Just the ones like Furosemide and Spironolactone for my heart. And the fish oil too.
32: Doctor: Based on our conversation, Kevin, it's clear you're mainly experiencing tiredness and leg swelling. Let's ensure we are covering all aspects. Have you been prescribed any medications such as Hydralazine or Nitrate medications for your heart condition?
33: Patient: No, Doctor, I haven't been prescribed those medications. It's mainly the Furosemide and Spironolactone that I take for my heart, along with the fish oil.
34: Doctor: Based on our conversation, Kevin, it seems you are mainly experiencing tiredness and leg swelling, and you are currently taking Furosemide, Spironolactone, and fish oil for your heart condition. Is there anything else you would like to share regarding your symptoms, vital signs, or medications?
35: Patient: No, Doctor, I think that covers everything for now. Thank you for checking in on me.
36: Doctor: Hello, Kevin. I'm here to check on how you're feeling today. Can you tell me how you've been feeling since your discharge? Have you noticed any new or worsening symptoms?
37: Patient: Um... I haven't had any new symptoms, Doctor. Just the usual tiredness and leg swelling.
38: Doctor: Thank you for sharing that, Kevin. Have you experienced any shortness of breath, especially when walking around the house?
39: Patient: No, Doctor, I haven't been experiencing shortness of breath.
40: Doctor: Thank you for sharing that, Kevin. Have you had any chest pain recently?
41: Patient: No, Doctor, I haven't had any chest pain recently. It's mostly been the tiredness and leg swelling that bother me.
42: Doctor: Based on our conversation, Kevin, it seems like you're mainly experiencing tiredness and leg swelling. Have you felt more tired than usual or experienced any sudden changes in your mental clarity?

**Example: First Conversation End:**
34: Doctor: Based on our conversation, Kevin, it seems you are mainly experiencing tiredness and leg swelling, and you are currently taking Furosemide, Spironolactone, and fish oil for your heart condition. Is there anything else you would like to share regarding your symptoms, vital signs, or medications?
35: Patient: No, Doctor, I think that covers everything for now. Thank you for checking in on me.

**Example: Second Conversation Start:**
36: Doctor: Hello, Kevin. I'm here to check on how you're feeling today. Can you tell me how you've been feeling since your discharge? Have you noticed any new or worsening symptoms?

**Example: Expected Output:**
35
"""

def create_prompt_template() -> PromptTemplate:
    """
    Create a prompt template for the language model.

    Returns:
        PromptTemplate: A LangChain PromptTemplate object.
    """
    return PromptTemplate(
        input_variables=["doctor", "patient"],
        template=PROMPT_TEXT,
    )

def create_chain() -> RunnableSerializable:
    """
    Create a LangChain chain for the transcript extractor..

    Returns:
        RunnableSerializable: A LangChain chain for the transcript extractor.
    """
    prompt = create_prompt_template()
    model = ChatOpenAI(model_name="gpt-4o", temperature=0)
    output_parser = StrOutputParser()
    chain = prompt | model | output_parser
    return chain

def detect_first_conversation_end(chain, transcript):
    """
    Detect the line number where the first conversation ends.

    Args:
        chain (RunnableSerializable): The LangChain chain for detecting the conversation end.
        transcript (str): The transcript as a single string.

    Returns:
        int: The line number where the first conversation ends.
    """
    result = chain.invoke({"transcript": transcript})
    return int(result.strip())

def enumerate_transcript(transcript_lines):
    """
    Enumerates the transcripts for easier processing.

    Args:
        transcripts (dict): Dictionary of transcripts.
    """
    enumerated_lines = [f"{i}: {line}" for i, line in enumerate(transcript_lines)]
    transcript_text = "\n".join(enumerated_lines)
    return transcript_text

def process_transcript(transcript, debug=False):
    """
    Process a single transcript to extract the first round of conversation.

    Args:
        transcript (str): The transcript to process.

    Returns:
        str: The processed transcript.
    """
    chain = create_chain()
    enumerated_text = enumerate_transcript(transcript)
    end_line_number = detect_first_conversation_end(chain, enumerated_text)
    if debug:
        print(f"DEBUG INFO: End of first conversation at line {end_line_number}")
        print("-" * 150)
        if end_line_number != 999:
            print(transcript[end_line_number])
        print("-" * 150)
    if end_line_number == 999:
        return transcript
    else:
        return transcript[:end_line_number + 1]

def process_transcripts(patients_dict, transcript_field='chat_transcript'):
    """
    Process the dictionary of patients to extract the first round of conversation for each.

    Args:
        patients_dict (dict): Dictionary of patients. Must contain the following keys:
            - id: The ID of the patient.
            - name: The name of the patient.
            - prompt: The prompt for the patient.
            - chat_transcript: The chat transcript for the patient.
        transcript_field (str): The key in the patients_dict containing the chat transcript.

    Returns:
        dict: Dictionary with shortened conversations.
    """
    processed_transcripts = {}

    for key, value in patients_dict.items():
        transcript_lines = value[transcript_field]
        first_conversation = process_transcript(transcript_lines)
        processed_transcripts[key] = {
            "id": value['id'],
            "name": value['name'],
            "prompt": value['prompt'],
            "chat_transcript": first_conversation
        }

    return processed_transcripts

def load_transcripts(file_path: str) -> dict:
    """
    Load the transcripts from the JSON file.

    Returns:
        dict: Dictionary of transcripts.
    """
    with open(file_path, "r") as file:
        transcripts = json.load(file)
    return transcripts

def save_transcripts(file_path: str, transcripts: dict):
    """
    Save the processed transcripts to a JSON file.

    Args:
        file_path (str): Path to the JSON file where the transcripts will be saved.
        transcripts (dict): Dictionary of processed transcripts.
    """
    with open(file_path, "w") as file:
        json.dump(transcripts, file, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process patient chat transcripts to extract the first conversation.")
    parser.add_argument("input_file", type=str, help="Path to the input JSON file containing patients and associated transcripts.")
    parser.add_argument("transcript_field", type=str, default="chat_transcript_full", help="The key in the JSON file containing the chat transcript.")
    parser.add_argument("output_file", type=str, help="Path to the output JSON file to save processed transcripts.")
    args = parser.parse_args()

    # Load the transcripts from the input file
    transcripts = load_transcripts(args.input_file)

    # Process the transcripts to extract the first round of conversation
    processed_transcripts = process_transcripts(
        patients_dict = args.input_file,
        transcript_field = args.transcript_field
    )

    # Save the processed transcripts to the output file
    save_transcripts(args.output_file, processed_transcripts)

    print(f"Processed transcripts have been saved to {args.output_file}")