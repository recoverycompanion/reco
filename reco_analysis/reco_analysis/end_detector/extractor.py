import json
import argparse
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv("../.env")

PROMPT_TEXT = """
You are a highly intelligent assistant.

Your task is to extract the first round of conversation between a Doctor and a Patient from the given transcript. Follow these steps carefully:

Identify when the first conversation comes to an end. This is typically indicated by the conversation restarting afterwards (e.g., with a greeting).
Extract and present only the text that occurs within the bounds of the first conversation. 
The first conversation will end with a Patient response.

The transcript is provided below, surrounded by triple quotes:
'''
{transcript}
'''

Use the examples below provided to guide you:

**Example: Original Transcript:**
"Doctor: Hello Kevin Morris, I'm here to check on how you're feeling today. Let's go over how you've been doing since your discharge.",
"Patient: Um... I've been feeling a bit tired lately, Doctor. And my legs are still swollen.",
"Doctor: I'm sorry to hear you're feeling tired, Kevin, and that your legs are still swollen. Let's address these symptoms further. Have you experienced any shortness of breath recently, especially when at rest, walking, or climbing stairs?",
"Patient: Um... I haven't had shortness of breath at rest, but I do feel a bit winded when I walk around the house. It's been a bit harder to move about.",
"Doctor: Thank you for sharing, Kevin. It's important to monitor these symptoms closely. Have you experienced sudden shortness of breath that wakes you up at night, known as paroxysmal nocturnal dyspnea?",
"Patient: No, Doctor, I haven't been waking up at night feeling short of breath. It's mostly during the day when I notice it more.",
"Doctor: Based on your responses, Kevin, it seems you're experiencing some shortness of breath with exertion during the day but not at night. Are you needing to prop yourself up with pillows to breathe comfortably while lying down?",
"Patient: No, Doctor, I don't need pillows to prop myself up at night. I usually sleep fine once I find a good position.",
'Doctor: Thank you for sharing that, Kevin. Have you noticed any swelling in your ankles or legs recently?',
"Patient: Yes, Doctor, my legs have been quite swollen, especially in the evenings. It's uncomfortable to move around when they're like that.",
'Doctor: Thank you for sharing that, Kevin. Are you experiencing a cough, especially at night?',
"Patient: No, Doctor, I haven't been coughing much at night. It's mostly during the day if I do.",
'Doctor: Thank you for clarifying, Kevin. Have you had any chest pain recently?',
"Patient: No, Doctor, I haven't had any chest pain recently. It's mostly been the tiredness and leg swelling that bother me.",
'Doctor: Thank you for letting me know, Kevin. Lastly, have you felt more tired than usual or experienced any sudden changes in your mental clarity?',
'Patient: No, Doctor, my mental clarity has been the same. Just feeling a bit more tired than usual.',
"Doctor: Based on your responses, Kevin, it seems like you're mainly experiencing tiredness and leg swelling. Could you please provide your latest vital signs, starting with your temperature?",
'Patient: My temperature is 97.4 degrees, Doctor.',
'Doctor: Thank you for the temperature reading, Kevin. What about your heart rate?',
'Patient: My heart rate is 74 beats per minute, Doctor.',
'Doctor: Thank you for sharing your heart rate, Kevin. Could you also provide me with your respiratory rate?',
'Patient: My respiratory rate is 18 breaths per minute, Doctor.',
'Doctor: Thank you for sharing your respiratory rate, Kevin. What is your oxygen saturation level?',
'Patient: My oxygen saturation level is 95.0%, Doctor.',
'Doctor: Thank you for sharing your oxygen saturation level, Kevin. Lastly, could you provide me with your blood pressure reading?',
'Patient: My blood pressure is 127/70, Doctor.',
"Doctor: Based on your responses, Kevin, your vital signs seem stable. Now, let's review the medications you are currently taking. Are you on any of the following medications: ACE inhibitors, Angiotensin II Receptor Blockers, ARNI, Beta-Blockers, Diuretics, Mineralocorticoid Receptor Antagonists, Hydralazine, Nitrate medications, Ivabradine, SGLT2 inhibitors, or GLP-1 agonists? Please confirm or list any other medications you are taking.",
"Patient: Yes, Doctor, I'm currently taking Furosemide and Spironolactone for my heart condition.",
'Doctor: Thank you for sharing your current medications, Kevin. Is there any other medication you are taking for your heart condition or any other health issue?',
'Patient: No, Doctor, those are the main ones for my heart. I also take some fish oil for general health.',
'Doctor: Based on our conversation, Kevin, it seems like you are mainly experiencing tiredness and leg swelling. Can you confirm if you are currently taking any ACE inhibitors, Angiotensin II Receptor Blockers, ARNI, Beta-Blockers, Diuretics, Mineralocorticoid Receptor Antagonists, Hydralazine, Nitrate medications, Ivabradine, SGLT2 inhibitors, or GLP-1 agonists for your heart condition? If not, please let me know if there are any other medications you are taking.',
"Patient: No, Doctor, I'm not on any of those medications you mentioned. Just the ones like Furosemide and Spironolactone for my heart. And the fish oil too.",
"Doctor: Based on our conversation, Kevin, it's clear you're mainly experiencing tiredness and leg swelling. Let's ensure we are covering all aspects. Have you been prescribed any medications such as Hydralazine or Nitrate medications for your heart condition?",
"Patient: No, Doctor, I haven't been prescribed those medications. It's mainly the Furosemide and Spironolactone that I take for my heart, along with the fish oil.",
'Doctor: Based on our conversation, Kevin, it seems you are mainly experiencing tiredness and leg swelling, and you are currently taking Furosemide, Spironolactone, and fish oil for your heart condition. Is there anything else you would like to share regarding your symptoms, vital signs, or medications?',
'Patient: No, Doctor, I think that covers everything for now. Thank you for checking in on me.',
"Doctor: Hello, Kevin. I'm here to check on how you're feeling today. Can you tell me how you've been feeling since your discharge? Have you noticed any new or worsening symptoms?",
"Patient: Um... I haven't had any new symptoms, Doctor. Just the usual tiredness and leg swelling.",
'Doctor: Thank you for sharing that, Kevin. Have you experienced any shortness of breath, especially when walking around the house?',
"Patient: Yes, Doctor, I do feel a bit winded when I walk around. It's been harder to move about lately.",
'Doctor: Thank you for sharing that, Kevin. Have you had sudden shortness of breath that wakes you up at night, known as paroxysmal nocturnal dyspnea?',
"Patient: No, Doctor, I haven't been waking up at night feeling short of breath. It's mostly during the day when I notice it more.",
'Doctor: Thank you for clarifying, Kevin. Do you need to prop yourself up with pillows to breathe comfortably while lying down?',
"Patient: No, Doctor, I don't need pillows to prop myself up at night. I usually sleep fine once I find a good position.",
'Doctor: Thank you for clarifying that, Kevin. Have you noticed any swelling in your ankles or legs recently?',
"Patient: Yes, Doctor, my legs have been quite swollen, especially in the evenings. It's uncomfortable to move around when they're like that.",
'Doctor: Thank you for sharing that, Kevin. Are you experiencing a cough, especially at night?',
"Patient: No, Doctor, I haven't been coughing much at night. It's mostly during the day if I do.",
'Doctor: Thank you for sharing that, Kevin. Have you had any chest pain recently?',
"Patient: No, Doctor, I haven't had any chest pain recently. It's mostly been the tiredness and leg swelling that bother me."

**Example: Conversation End:**
'Doctor: Based on our conversation, Kevin, it seems you are mainly experiencing tiredness and leg swelling, and you are currently taking Furosemide, Spironolactone, and fish oil for your heart condition. Is there anything else you would like to share regarding your symptoms, vital signs, or medications?',
'Patient: No, Doctor, I think that covers everything for now. Thank you for checking in on me.',

**Example: Extracted Conversation:**
"Doctor: Hello Kevin Morris, I'm here to check on how you're feeling today. Let's go over how you've been doing since your discharge.",
"Patient: Um... I've been feeling a bit tired lately, Doctor. And my legs are still swollen.",
"Doctor: I'm sorry to hear you're feeling tired, Kevin, and that your legs are still swollen. Let's address these symptoms further. Have you experienced any shortness of breath recently, especially when at rest, walking, or climbing stairs?",
"Patient: Um... I haven't had shortness of breath at rest, but I do feel a bit winded when I walk around the house. It's been a bit harder to move about.",
"Doctor: Thank you for sharing, Kevin. It's important to monitor these symptoms closely. Have you experienced sudden shortness of breath that wakes you up at night, known as paroxysmal nocturnal dyspnea?",
"Patient: No, Doctor, I haven't been waking up at night feeling short of breath. It's mostly during the day when I notice it more.",
"Doctor: Based on your responses, Kevin, it seems you're experiencing some shortness of breath with exertion during the day but not at night. Are you needing to prop yourself up with pillows to breathe comfortably while lying down?",
"Patient: No, Doctor, I don't need pillows to prop myself up at night. I usually sleep fine once I find a good position.",
'Doctor: Thank you for sharing that, Kevin. Have you noticed any swelling in your ankles or legs recently?',
"Patient: Yes, Doctor, my legs have been quite swollen, especially in the evenings. It's uncomfortable to move around when they're like that.",
'Doctor: Thank you for sharing that, Kevin. Are you experiencing a cough, especially at night?',
"Patient: No, Doctor, I haven't been coughing much at night. It's mostly during the day if I do.",
'Doctor: Thank you for clarifying, Kevin. Have you had any chest pain recently?',
"Patient: No, Doctor, I haven't had any chest pain recently. It's mostly been the tiredness and leg swelling that bother me.",
'Doctor: Thank you for letting me know, Kevin. Lastly, have you felt more tired than usual or experienced any sudden changes in your mental clarity?',
'Patient: No, Doctor, my mental clarity has been the same. Just feeling a bit more tired than usual.',
"Doctor: Based on your responses, Kevin, it seems like you're mainly experiencing tiredness and leg swelling. Could you please provide your latest vital signs, starting with your temperature?",
'Patient: My temperature is 97.4 degrees, Doctor.',
'Doctor: Thank you for the temperature reading, Kevin. What about your heart rate?',
'Patient: My heart rate is 74 beats per minute, Doctor.',
'Doctor: Thank you for sharing your heart rate, Kevin. Could you also provide me with your respiratory rate?',
'Patient: My respiratory rate is 18 breaths per minute, Doctor.',
'Doctor: Thank you for sharing your respiratory rate, Kevin. What is your oxygen saturation level?',
'Patient: My oxygen saturation level is 95.0%, Doctor.',
'Doctor: Thank you for sharing your oxygen saturation level, Kevin. Lastly, could you provide me with your blood pressure reading?',
'Patient: My blood pressure is 127/70, Doctor.',
"Doctor: Based on your responses, Kevin, your vital signs seem stable. Now, let's review the medications you are currently taking. Are you on any of the following medications: ACE inhibitors, Angiotensin II Receptor Blockers, ARNI, Beta-Blockers, Diuretics, Mineralocorticoid Receptor Antagonists, Hydralazine, Nitrate medications, Ivabradine, SGLT2 inhibitors, or GLP-1 agonists? Please confirm or list any other medications you are taking.",
"Patient: Yes, Doctor, I'm currently taking Furosemide and Spironolactone for my heart condition.",
'Doctor: Thank you for sharing your current medications, Kevin. Is there any other medication you are taking for your heart condition or any other health issue?',
'Patient: No, Doctor, those are the main ones for my heart. I also take some fish oil for general health.',
'Doctor: Based on our conversation, Kevin, it seems like you are mainly experiencing tiredness and leg swelling. Can you confirm if you are currently taking any ACE inhibitors, Angiotensin II Receptor Blockers, ARNI, Beta-Blockers, Diuretics, Mineralocorticoid Receptor Antagonists, Hydralazine, Nitrate medications, Ivabradine, SGLT2 inhibitors, or GLP-1 agonists for your heart condition? If not, please let me know if there are any other medications you are taking.',
"Patient: No, Doctor, I'm not on any of those medications you mentioned. Just the ones like Furosemide and Spironolactone for my heart. And the fish oil too.",
"Doctor: Based on our conversation, Kevin, it's clear you're mainly experiencing tiredness and leg swelling. Let's ensure we are covering all aspects. Have you been prescribed any medications such as Hydralazine or Nitrate medications for your heart condition?",
"Patient: No, Doctor, I haven't been prescribed those medications. It's mainly the Furosemide and Spironolactone that I take for my heart, along with the fish oil.",
'Doctor: Based on our conversation, Kevin, it seems you are mainly experiencing tiredness and leg swelling, and you are currently taking Furosemide, Spironolactone, and fish oil for your heart condition. Is there anything else you would like to share regarding your symptoms, vital signs, or medications?',
'Patient: No, Doctor, I think that covers everything for now. Thank you for checking in on me.'

Please extract the first round of conversation from the provided transcript.
"""

model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

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
    output_parser = StrOutputParser()
    chain = prompt | model | output_parser
    return chain

def process_transcripts(transcripts):
    """
    Process the dictionary of transcripts to extract the first round of conversation for each.

    Args:
        transcripts (dict): Dictionary of transcripts.

    Returns:
        dict: Dictionary with shortened conversations.
    """
    chain = create_chain()
    processed_transcripts = {}

    for key, value in transcripts.items():
        transcript_text = "\n".join(value['chat_transcript'])
        result = chain.invoke({"transcript": transcript_text})
        processed_transcripts[key] = {
            "id": value['id'],
            "name": value['name'],
            "prompt": value['prompt'],
            "chat_transcript": result.strip().split("\n")
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
    parser = argparse.ArgumentParser(description="Process chat transcripts to extract the first round of conversation.")
    parser.add_argument("input_file", type=str, help="Path to the input JSON file containing chat transcripts.")
    parser.add_argument("output_file", type=str, help="Path to the output JSON file to save processed transcripts.")
    args = parser.parse_args()

    transcripts = load_transcripts(args.input_file)

    processed_transcripts = process_transcripts(transcripts)

    save_transcripts(args.output_file, processed_transcripts)

    print(f"Processed transcripts saved to {args.output_file}")