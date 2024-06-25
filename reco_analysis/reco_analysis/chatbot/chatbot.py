"""
chatbot.py

This module implements the `DialogueAgent` class, a conversational agent for simulating dialogues between a doctor and a patient.
It leverages the `langchain` framework and the `ChatOpenAI` model to generate responses based on conversation history.

Classes:
    DialogueAgent: Manages the conversation, including initializing with a specific role, handling message flow,
                   generating responses, and storing conversation history.

Variables:
    session_store (dict): An in-memory dictionary for storing chat histories to enable stateful conversations.
    model (ChatOpenAI): The language model instance used for generating responses.

Usage:
    agent = DialogueAgent(role="Doctor")
    agent.receive("I've been feeling tired.")
    response = agent.generate_response()
    print(response)

Components:
------------
- DialogueAgent:
    Manages the conversation flow, including:
    - Initializing with a specific role (Doctor or Patient) and session context.
    - Handling the flow of messages.
    - Generating and responding to inputs using the `ChatOpenAI` model.
    - Storing conversation history for continuity.

- Session Store:
    A temporary in-memory dictionary (`session_store`) for storing chat histories, enabling stateful conversations.

- Prompt Templates:
    Predefined prompts set the context and guide the conversation, using templates that include system messages and placeholders for user input and history.

    Note: System messages and AI guidance should be defined in `prompts.py`, which includes templates for different roles and contexts.

Example:
---------
    agent = DialogueAgent(role="Doctor")
    agent.receive("I've been feeling tired.")
    response = agent.generate_response()
    print(response)

Notes:
-------
- Ensure environment variables, especially API keys, are set up using a `.env` file.
- Define system messages and AI guidance in `prompts.py`.
- This code is typically copied from `notebooks/chatbot.ipynb` to `reco_analysis/reco_analysis/chatbot.py`.

"""

import uuid
from dotenv import load_dotenv
from typing import Optional, List
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.schema import BaseChatMessageHistory
from reco_analysis.chatbot.prompts import system_message_doctor, ai_guidance_doctor, ai_guidance_patient

# Load environment variables
load_dotenv("../.env")

# Define the session store (using a dictionary to store chat histories in memory for now)
session_store = {}

def get_session_history(session_id: str, session_store: dict) -> BaseChatMessageHistory:
    """
    Store the chat history for a given session ID.
    
    Args:
        session_id (str): The session ID to retrieve the chat history for.
        session_store (dict): The dictionary to store the chat histories.
    
    Returns:
        BaseChatMessageHistory: The chat history for the session.
    """
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]

model = ChatOpenAI(temperature=0.7, model_name='gpt-3.5-turbo')

class DialogueAgent:
    def __init__(self,
                 role: Optional[str] = "Doctor",
                 system_message: Optional[str] = system_message_doctor,
                 model: Optional[ChatOpenAI] = model,
                 session_id: Optional[str] = None) -> None:
        """
        Initialize the DialogueAgent with a name, system message, guidance after each run of the chat,
        a language model, and a session ID.
        
        Args:
            role (str): The role of the agent (either 'Patient' or 'Doctor').
            system_message (str): The initial system message to set the context.
            model (ChatOpenAI): The language model to use for generating responses.
            session_id (str, optional): The unique session ID for the conversation. Defaults to None. If None, a new session ID will be generated. If a session ID is provided, the conversation history will be loaded from the session store (if available)
        """
        self.system_message = system_message
        self.model = model

        # Set the role of the agent and the human
        role = role.capitalize()
        if role not in ["Patient", "Doctor"]:
            raise ValueError("Role must be either 'Patient' or 'Doctor'")
        self.role = role
        self.human_role = "Doctor" if self.role == "Patient" else "Patient"

        # Generate a unique conversation ID if one is not provided
        self.session_id = str(uuid.uuid4()) if session_id is None else session_id

        # Initialize chat message history to keep track of the entire conversation
        self.memory = get_session_history(self.session_id, session_store)
        
        # Define the prompt template with placeholders for the chat history and human input
        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=self.system_message),  # The persistent system prompt
                MessagesPlaceholder(variable_name="chat_history"),  # Where the memory will be stored.
                HumanMessagePromptTemplate.from_template("{human_input}"),  # Where the human input will be injected
            ]
        )
        
        # Define the LLM chain with the model and prompt
        self.chain = self.prompt | self.model | StrOutputParser()

        # Prepare the AI instruction (this acts as guidance for the agent after each run of the chat)
        self.ai_instruct = ai_guidance_doctor if self.role == "Doctor" else ai_guidance_patient

    def reset(self) -> None:
        """
        Resets the conversation history in memory
        """
        self.memory.clear()

    def generate_response(self) -> str:
        """
        Generates a response based on the conversation history stored in memory.
        
        Returns:
            str: The response generated by the language model.
        """
        # Prepare the input for the model
        input_data = {
            "chat_history": self.memory.messages,
            "human_input": self.ai_instruct
        }

        # Run the chain to generate a response
        response = self.chain.invoke(input_data)

        # Save the AI's response to the memory
        self.send(response)

        return response
    
    def send(self, message: str) -> None:
        """
        Adds a new message to the conversation history in memory for the AI role.

        Args:
            message (str): The content of the message.
        """
        # Save the AI response to the conversation memory
        self.memory.add_message(AIMessage(content=message, name=self.role))

    def receive(self, message: str) -> None:
        """
        Adds a new message to the conversation history in memory for the human role.
        
        Args:
            message (str): The content of the message.
        """
        # Save the user input to the conversation memory
        self.memory.add_message(HumanMessage(content=message, name=self.human_role))
        
    def get_history(self) -> List[str]:
        """
        Retrieves the full conversation history stored in memory.
        
        Returns:
            List[str]: The list of messages in the conversation history.
        """
        formatted_history = []
        for msg in self.memory.messages:
            if isinstance(msg, HumanMessage):
                formatted_history.append(f"{self.human_role}: {msg.content}")
            elif isinstance(msg, AIMessage):
                formatted_history.append(f"{self.role}: {msg.content}")
            else:
                formatted_history.append(f"System: {msg.content}")
        return formatted_history