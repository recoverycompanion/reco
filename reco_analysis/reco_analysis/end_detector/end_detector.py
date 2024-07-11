# Import necessary modules
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the prompt template text
PROMPT_TEXT = """
You are analyzing a conversation between a doctor and a patient. Your task is to determine if the conversation is coming to a close based on the Doctor and the Patient. Respond with 'True' if the conversation is coming to a close, and 'False' otherwise.

Follow the provided examples to understand the criteria:

### Example 1:
**Doctor:** Based on our conversation, Kevin, it seems you are mainly experiencing tiredness and leg swelling, and you are currently taking Furosemide, Spironolactone, and fish oil for your heart condition. Is there anything else you would like to share regarding your symptoms, vital signs, or medications?  
**Patient:** No, Doctor, I think that covers everything for now. Thank you for checking in on me.  
**Response:** True

### Example 2:
**Doctor:** Based on our conversation, Kevin, it seems like you are mainly experiencing tiredness and leg swelling. Could you please provide your latest vital signs, starting with your temperature?  
**Patient:** My temperature is 97.4 degrees, Doctor.  
**Response:** False

### Example 3:
**Doctor:** Thank you for sharing your oxygen saturation level, Kevin. Lastly, could you provide me with your blood pressure reading?  
**Patient:** My blood pressure is 127/70, Doctor.  
**Response:** False

### Example 4:
**Doctor:** Thank you for sharing your current medications, Kevin. Is there any other medication you are taking for your heart condition or any other health issue?  
**Patient:** No, Doctor, those are the main ones for my heart. I also take some fish oil for general health.  
**Response:** False

### Example 5:
**Doctor:** Thank you for sharing your respiratory rate, Gregory. Could you now provide your oxygen saturation level for me?  
**Patient:** My oxygen saturation level is 99.0, Doctor. It's good to see that it's in a healthy range.  
**Response:** False

### Example 6:
**Doctor:** Thank you for sharing about your medications. It's important to continue taking them as prescribed. Please remember to reach out to your healthcare provider if you notice any significant changes or worsening of symptoms. If you have any further concerns or questions, feel free to share them with me.
**Patient:** Thank you, Doctor. Um... I will definitely reach out if I notice any changes. I appreciate your help and advice.  
**Response:** True

### Example 7:
**Doctor:** Thank you for sharing your blood pressure, Maria. Lastly, could you provide me with your current weight?  
**Patient:** I'm sorry, Doctor, I don't have a scale at home to check my weight.  
**Response:** False

### Example 8:
**Doctor:** Thank you for sharing your current medications, Jennifer. Are you taking any other medications apart from Beta-Blockers and Diuretics?  
**Patient:** No, Doctor, those are the main ones I'm taking right now. Um... I try to remember to take them at the right times every day.  
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