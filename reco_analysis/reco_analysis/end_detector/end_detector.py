# Import necessary modules
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the prompt template text
PROMPT_TEXT = """
You are analyzing snippets from a conversation between a doctor and a patient. Your task is to determine if the conversation is coming to a close based on the Doctor and the Patient. Respond with 'True' if the conversation is coming to a close, and 'False' otherwise.

### Patterns indicating a continuation:
1. Doctor asking for more information, even if it includes terms like 'lastly' or 'finally'.
2. Patient providing additional information.
3. Patient asking questions.

### Patterns indicating a closing:
1. Doctor explicitly saying "Goodbye."
2. Patient explicitly saying "Goodbye."
2. Doctor providing final instructions or reminders.
3. Doctor providing encouragement for future contact.
4. Patient saying that they will make further contact if needed.
5. Doctor expressing care and well wishes.
6. Doctor asking if the Patient has any more questions or concerns.
7. Patient stating that they don't have any more questions or concerns.

Follow the provided examples to understand the criteria:

### Example 1:
**Doctor:** Based on our conversation, Kevin, it seems you are mainly experiencing tiredness and leg swelling, and you are currently taking Furosemide, Spironolactone, and fish oil for your heart condition. Is there anything else you would like to share regarding your symptoms, vital signs, or medications?  
**Patient:** No, Doctor, I think that covers everything for now. Thank you for checking in on me.  
**Response:** True

### Example 2:
**Doctor:** Based on our conversation, Kevin, it seems like you are mainly experiencing tiredness and leg swelling. Could you please provide your latest vital signs, starting with your temperature?  
**Patient:** My temperature is 97.4 degrees, Doctor.  
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
    chain = create_chain()
    result = chain.invoke({"doctor": doctor_input, "patient": patient_input})
    return result.strip().lower() == 'true'