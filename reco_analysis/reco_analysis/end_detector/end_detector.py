import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

# End terms
END_TERMS = {
    "goodbye",
    "bye",
    "take care",
    "see you later",
    "farewell",
    "talk to you soon",
    "see you",
    "later",
    "have a good day",
    "have a nice day",
    "catch you later",
    "until next time",
    "peace out",
    "all the best",
    "best regards",
    "good night",
    "see ya",
    "take it easy",
    "cheers"
}

# Define the prompt template text
PROMPT_TEXT = """
You are analyzing a snippet from a conversation between a doctor and a patient. Your task is to determine if the conversation is coming to a close based on the Doctor and the Patient.
Respond with 'True' if the conversation is coming to a close, and 'False' otherwise.

### Patterns indicating a continuation:
1. Doctor asking for more information.
2. Patient providing additional information.
3. Patient asking questions.

### Patterns indicating a closing:
1. Doctor providing final instructions or reminders.
2. Doctor providing encouragement for future contact.
3. Patient saying that they will make further contact if needed.
4. Doctor expressing care and well wishes.
5. Doctor asking if the Patient has any more questions or concerns.
6. Patient stating that they don't have any more questions or concerns.

Follow the provided examples to understand the criteria:

### Example 1:
**Doctor:** Is there anything else you would like to share regarding your symptoms, vital signs, or medications?  
**Patient:** No, Doctor, I think that covers everything for now. Thank you for checking in on me.  
**Response:** True

### Example 2:
**Doctor:** If you have any concerns or notice any changes, please remember to contact your healthcare provider. Thank you for sharing your updates with me today. If you have any more questions or need further assistance, feel free to reach out. Take care, and continue monitoring your recovery closely. Goodbye.
**Patient:** Thank you, Doctor. I appreciate your help and advice. Um, I'll make sure to reach out if anything changes or if I have any concerns. Take care and goodbye..
**Response:** True

### Example 3:
**Doctor:** Based on our conversation, Kevin, it seems like you are mainly experiencing tiredness and leg swelling. Could you please provide your latest vital signs, starting with your temperature?  
**Patient:** My temperature is 97.4 degrees, Doctor.  
**Response:** False

### Example 4:
**Doctor:** Thank you for sharing your respiratory rate, Gregory. Could you now provide your oxygen saturation level for me?  
**Patient:** My oxygen saturation level is 99.0, Doctor. It's good to see that it's in a healthy range.  
**Response:** False

Now, analyze the following conversation and determine if it is coming to a close:

**Doctor:**  
```{doctor}```  

**Patient:**  
```{patient}```
"""

# Initialize the language model and output parser
model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
output_parser = StrOutputParser()

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

def create_chain() -> 'LLMChain':
    """
    Create a LangChain chain for the end terminator.

    Returns:
        LLMChain: A LangChain chain for the end terminator.
    """
    prompt = create_prompt_template()
    chain = prompt | model | output_parser
    return chain

def contains_closing_terms(text: str, closing_terms: list[str]) -> bool:
    """
    Check if the text contains any of the closing terms.

    Args:
        text (str): The text to check for closing terms.
        closing_terms (list[str]): A list of closing terms to check for.

    Returns:
        bool: True if the text contains any of the closing terms, False otherwise.
    """
    if text is None:
        return False
    else:
        for term in closing_terms:
            if re.search(rf"\b{term}\b", text, re.IGNORECASE):
                return True
        return False

def detect_end(doctor_input: str, patient_input: str) -> bool:
    """
    Check if the conversation is coming to a close based on the last doctor input and patient input.
    Note that the sequence within the conversation has to be doctor input followed by patient input.

    Args:
        chain (LLMChain): The LangChain chain to process the input.
        doctor_input (str): The last doctor input.
        patient_input (str): The last patient input.

    Returns:
        bool: True if the conversation is coming to a close, False otherwise.
    """
    # Check for closing terms
    if contains_closing_terms(doctor_input, END_TERMS) or contains_closing_terms(patient_input, END_TERMS):
        return True
    
    # If no closing terms are found, use the language model to detect the end
    chain = create_chain()
    result = chain.invoke({"doctor": doctor_input, "patient": patient_input})
    return result.strip().lower() == 'true'

# Example usage
if __name__ == "__main__":
    doctor_input = "Based on our conversation, Kevin, it seems you are mainly experiencing tiredness and leg swelling, and you are currently taking Furosemide, Spironolactone, and fish oil for your heart condition. Is there anything else you would like to share regarding your symptoms, vital signs, or medications?"
    patient_input = "Goodbye"
    
    is_conversation_ending = detect_end(doctor_input, patient_input)
    print(is_conversation_ending)  # Should print: True

    # Additional test cases
    test_cases = [
        ("Do you have any more questions?", "No, doctor. Goodbye.", True),
        ("Could you please provide your latest vital signs?", "My temperature is 98.6 degrees.", False),
        ("Is there anything else you would like to discuss?", "No, I think that's all for now.", True),
        ("Please follow up with your primary care physician.", "I will. Thank you, doctor. See you later.", True)
    ]

    for doctor_input, patient_input, expected in test_cases:
        result = detect_end(doctor_input, patient_input)
        print(f"Doctor: {doctor_input}\nPatient: {patient_input}\nExpected: {expected}, Got: {result}\n")