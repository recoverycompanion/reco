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

PROMPT_TEXT = """
You are an intelligent assistant tasked with identifying the line number where the first round of conversation ends in a transcript between a Doctor and a Patient.

It is very important that you only output a number:
- **Case 1: First conversation does not end**: If there is no end to the first conversation, output 999.
- **Case 2: First conversation ends**: If the first conversation ends, output the line number of the last line of the first conversation.

Follow these steps:
<steps>
1. Identify the first conversation's end, if applicable:
   - Look for a closing statement by the Doctor followed by a confirmation from the Patient indicating the conversation has reached a conclusion.
   - The last line of the first conversation is always spoken by the Patient.
   - The last line of the first conversation is always an odd line number.
   - The last line of the first conversation will not contain a greeting or welcoming phrase typically used to start conversations.
2. Identify the second conversation's start, if applicable:
   - Look for a Doctor greeting the Patient again, e.g., "Hello [Patient name], ello Javier Rivas, I'm here to follow up on your health since our last conversation. How have you been feeling recently? Any new or worsening symptoms you'd like to discuss today?
   - The first line of the second conversation is always spoken by the Doctor.
   - The second conversation always starts with an even line number.
3. If **Case 1 (first conversation does not end)** applies:
   - Output 999.
4. If **Case 2 (first conversation ends)** applies:
   - Confirm that the end of the first conversation appears immediately before the start of the second conversation and output the line number of the last line of the first conversation.
   - Otherwise, output 999.
</steps>
    
The transcript is provided below, surrounded by triple quotes:
'''
{transcript}
'''

Use this example to understand **Case 1: First conversation does not end**:
<example 1>
**Transcript:**
0: Doctor: Hello Michelle Graham, I'm here to check on how you're feeling today. Let's go over how you've been doing since your discharge.
1: Patient: I'm not feeling too bad, just trying to take it easy. It's been a bit of a struggle adjusting after being in the hospital.
2: Doctor: I'm glad to hear you're trying to take it easy, Michelle. Can you tell me how you've been feeling today? Have you noticed any new or worsening symptoms?
3: Patient: I don't remember exactly how I've been feeling today. It's hard to say if there have been any new symptoms. Maybe it's just the usual fatigue and shortness of breath.
4: Doctor: Thank you for sharing, Michelle. Let's delve a bit deeper into your symptoms. Have you experienced any shortness of breath? If yes, does it occur at rest, when walking, or when climbing stairs?
5: Patient: I can't quite describe this. I'm not sure what you're asking. Let me think... I guess I feel a bit out of breath sometimes when I'm walking around. It's hard to say exactly when it happens.
6: Doctor: Thank you for sharing, Michelle. Have you had sudden shortness of breath that wakes you up at night recently?
7: Patient: I'd rather not say if I've had shortness of breath at night. Can we talk about something else?
8: Doctor: I understand, Michelle. Let's focus on another aspect. Do you need to prop yourself up with pillows to breathe comfortably while lying down?
9: Patient: I'm not sure if I need pillows to prop myself up. I don't think that's important right now. Is this really necessary to discuss?
10: Doctor: I apologize for any discomfort, Michelle. Let's move on to another topic. Could you please provide your latest vital signs, starting with your temperature?
11: Patient: I can't quite remember my exact temperature, but I think it was around 98.2. I'm not sure if that's normal or not.
12: Doctor: Thank you for sharing your temperature, Michelle. Next, could you please provide your heart rate?
13: Patient: I'm not sure about my heart rate, but I think it was around 89. I'm unfamiliar with what's considered normal for that.
14: Doctor: Thank you for sharing your heart rate, Michelle. Lastly, could you please provide your blood pressure readings?

**Expected Output:**
999
</example 1>

Use this example to understand **Case 2: First conversation ends**:
<example 2>
**Transcript:**
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
10: Based on our conversation, Kevin, it seems you are mainly experiencing tiredness and leg swelling. Is there anything else you would like to share?
11: Patient: No, Doctor, I think that covers everything for now. Thank you for checking in on me.
12: Doctor: Hello, Kevin. I'm here to check on how you're feeling today. Can you tell me how you've been feeling since your discharge? Have you noticed any new or worsening symptoms?
13: Patient: Um... I haven't had any new symptoms, Doctor. Just the usual tiredness and leg swelling.
14: Doctor: I'm sorry to hear you're still experiencing tiredness and leg swelling, Kevin. Let's address these symptoms further.

**First Conversation End:**
11: Patient: No, Doctor, I think that covers everything for now. Thank you for checking in on me.

**Second Conversation Start:**
12: Doctor: Hello, Kevin. I'm here to check on how you're feeling today. Can you tell me how you've been feeling since your discharge? Have you noticed any new or worsening symptoms?

**Expected Output:**
11
</example 2>
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
    model = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
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

def process_transcripts(patients_dict, transcript_field='chat_transcript', debug=False):
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
        if debug:
            print("\n")
            print(f"Processing transcript for {value['name']}...")
            print("=" * 150)
            for i, line in enumerate(transcript_lines):
                print(f"{i}: {line}")
            print("\n")
        first_conversation = process_transcript(transcript_lines, debug=debug)
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