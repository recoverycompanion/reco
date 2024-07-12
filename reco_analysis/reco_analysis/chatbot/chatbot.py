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

import json
import os
import typing
import uuid

from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema import (
    AIMessage,
    BaseChatMessageHistory,
    HumanMessage,
    SystemMessage,
)
from langchain.schema.output_parser import StrOutputParser
from langchain_community.chat_message_histories import (
    ChatMessageHistory,
    SQLChatMessageHistory,
)
from langchain_community.chat_message_histories.sql import DefaultMessageConverter
from langchain_core.messages import BaseMessage, message_to_dict
from langchain_core.prompts import HumanMessagePromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from reco_analysis.chatbot.prompts import (
    ai_guidance_doctor,
    ai_guidance_patient,
    system_message_doctor,
)
from reco_analysis.data_model import data_models
from reco_analysis.end_detector.end_detector import detect_end

session = data_models.get_session()

# Load environment variables
load_dotenv("../.env")

# if postgres variables are specified, set `use_postgres` to True
use_postgres = data_models.connection_env_vars_available()


class CustomMessageConverter(DefaultMessageConverter):
    def __init__(self):
        self.model_class = data_models.Message

    def to_sql_model(self, message: BaseMessage, session_id: str) -> data_models.Message:
        return self.model_class(
            session_id=session_id, message=json.dumps(message_to_dict(message))
        )

    def get_sql_model_class(self):
        return data_models.Message


# For local dev - define the session store (a dictionary to store chat histories in memory)
SESSION_STORE: typing.Dict[str, BaseChatMessageHistory] = {}

postgres_engine = data_models.get_engine()


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Store the chat history for a given session ID.

    Args:
        session_id (str): The session ID to retrieve the chat history for.

    Returns:
        BaseChatMessageHistory: The chat history for the session.
    """

    if use_postgres:
        return SQLChatMessageHistory(
            session_id=session_id,
            connection=postgres_engine,
            session_id_field_name="session_id",
            custom_message_converter=CustomMessageConverter(),
        )
    else:
        if session_id not in SESSION_STORE:
            SESSION_STORE[session_id] = ChatMessageHistory()
        return SESSION_STORE[session_id]


model = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo")


class DialogueAgent:
    def __init__(
        self,
        patient_id: int,
        role: typing.Optional[str] = "Doctor",
        system_message: typing.Optional[str] = system_message_doctor,
        model: typing.Optional[ChatOpenAI] = model,
        session_id: typing.Optional[str] = None,
    ) -> None:
        """
        Initialize the DialogueAgent with a name, system message, guidance after each run of the chat,
        a language model, and a session ID.

        Args:
            role (str): The role of the agent (either 'Patient' or 'Doctor').
            system_message (str): The initial system message to set the context.
            model (ChatOpenAI): The language model to use for generating responses.
            patient_id (str, optional): The unique patient ID for the conversation. Defaults to None.
            session_id (str, optional): The unique session ID for the conversation. Defaults to None. If None, a new session ID will be generated. If a session ID is provided, the conversation history will be loaded from the session store (if available)
        """
        self.system_message = system_message
        self.model = model

        # Set the patient ID
        self.patient: data_models.Patient = data_models.Patient.get_by_id(patient_id, session)

        # Set the role of the agent and the human
        role = role.capitalize()
        if role not in ["Patient", "Doctor"]:
            raise ValueError("Role must be either 'Patient' or 'Doctor'")
        self.role = role
        self.human_role = "Doctor" if self.role == "Patient" else "Patient"

        # Generate a unique conversation ID if one is not provided
        if session_id is None:
            # create session
            self.conversation_session = data_models.ConversationSession.new_session(
                patient_id=self.patient.id, session=session
            )
            self.session_id = self.conversation_session.id
        else:
            self.session_id = session_id
            self.conversation_session = data_models.ConversationSession.get_by_id(
                session_id, session
            )

        # Initialize chat message history to keep track of the entire conversation
        self.memory: BaseChatMessageHistory = get_session_history(self.session_id)

        # Define the prompt template with placeholders for the chat history and human input
        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=self.system_message),  # The persistent system prompt
                MessagesPlaceholder(
                    variable_name="chat_history"
                ),  # Where the memory will be stored.
                HumanMessagePromptTemplate.from_template(
                    "{human_input}"
                ),  # Where the human input will be injected
            ]
        )

        # Define the LLM chain with the model and prompt
        self.chain = self.prompt | self.model | StrOutputParser()

        # Prepare the AI instruction (this acts as guidance for the agent after each run of the chat)
        self.ai_instruct = ai_guidance_doctor if self.role == "Doctor" else ai_guidance_patient

        # Initialize end of conversation flag
        self.end_conversation = False

    def reset(self) -> None:
        """
        Resets the conversation history in memory
        """
        self.memory.clear()
        self.end_conversation = False

    def get_last_doctor_patient_messages(self) -> typing.Tuple[str, str]:
        """
        Retrieves the last doctor and patient messages from the conversation history.
        
        Returns:
            Tuple[str, str]: A tuple containing the last doctor and patient messages.
        """
        last_doctor_message = None
        last_patient_message = None

        if len(self.memory.messages) >= 2 and self.memory.messages[-1].name == 'Patient' and self.memory.messages[-2].name == 'Doctor':
            last_doctor_message = self.memory.messages[-2].content
            last_patient_message = self.memory.messages[-1].content

        return last_doctor_message, last_patient_message
    
    def detect_and_handle_end(self) -> None:
        """
        Detects the end of the conversation based on the last doctor and patient messages.
        """
        last_doctor_message, last_patient_message = self.get_last_doctor_patient_messages()
        self.end_conversation = detect_end(doctor_input=last_doctor_message, patient_input=last_patient_message)

    def generate_response(self) -> str:
        """
        Generates a response based on the conversation history stored in memory.

        Returns:
            str: The response generated by the language model.
        """
        # Prepare the input for the model
        input_data = {
            "chat_history": self.memory.messages,
            "human_input": self.ai_instruct,
        }

        # Run the chain to generate a response
        response = self.chain.invoke(input_data)

        # Save the AI's response to the memory
        self.send(response)

        # Detect and handle the end of the conversation if the role is Patient
        self.detect_and_handle_end() if self.role == 'Patient' else None

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

        # Detect end of conversation if the role is Doctor
        self.detect_and_handle_end() if self.role == 'Doctor' else None

    def get_history(self) -> typing.List[str]:
        """
        Retrieves the full conversation history stored in memory.

        Returns:
            typing.List[str]: The list of messages in the conversation history.
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

    def get_latest_message_role(self) -> str | None:
        """
        Get the role of the speaker of the latest message in the conversation history.

        Returns:
            str: The role of the speaker of the latest message.
        """
        if self.memory.messages:
            latest_message = self.memory.messages[-1]
            if isinstance(latest_message, HumanMessage):
                return self.human_role
            elif isinstance(latest_message, AIMessage):
                return self.role

        # If no messages are present
        return None