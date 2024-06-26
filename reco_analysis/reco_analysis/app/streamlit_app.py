"""
streamlit_app.py

This module defines a Streamlit application for the RECO Consultation chatbot.
The application simulates a conversation between a virtual doctor and a patient, using the `DialogueAgent` class to manage the dialogue flow and generate responses.

Functions:
----------
- stream_response(role, response_text):
    Streams the response text word by word with a slight delay to simulate typing.
    
    Args:
        role (str): The role of the speaker ("Doctor" or "Patient").
        response_text (str): The full response text to stream.

- main():
    Sets up and runs the Streamlit interface for the chatbot, handling the interaction flow and session state.
    - Initializes the `DialogueAgent` and manages session state.
    - Displays chat history and handles user input.
    - Generates responses based on the conversation flow.
    - Allows the user to end the conversation and save the chat history to a file.

Usage:
------
To run this Streamlit application, execute the following command in the terminal:
    streamlit run streamlit_app.py
"""

import streamlit as st
from dotenv import load_dotenv
from reco_analysis.chatbot.chatbot import DialogueAgent
from langchain_openai import ChatOpenAI
import time
from pathlib import Path
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

def load_credentials(file_path):
    """
    Load credentials from a YAML file.

    Args:
        file_path (str): The path to the YAML file containing the credentials.
    
    Returns:
        dict: A dictionary containing the credentials.
    """
    with open(file_path, "r") as file:
        credentials = yaml.load(file, Loader=SafeLoader)
    return credentials


def setup_authenticator():
    """
    Set up the authenticator for the Streamlit application.

    Returns:
        tuple: A tuple containing the authenticator object, the user's name, the authentication status, and the username (i.e., the patient ID)
    """
    # Load credentials from the YAML file
    credentials_path = Path(__file__).parent / 'credentials.yaml'
    credentials = load_credentials(credentials_path)

    # Create an authentication object
    authenticator = stauth.Authenticate(
        credentials['credentials'],
        credentials['cookie']['name'],
        credentials['cookie']['key'],
        credentials['cookie']['expiry_days'],
        credentials.get('pre-authorized', None)
    )

    name, authentication_status, patient_id = authenticator.login(
        location='main',
        fields={'Form name': 'Login', 'Username': 'Patient ID', 'Password': 'Password', 'Login': 'Login'}
    )

    return authenticator, name, authentication_status, patient_id

def stream_response(role, response_text):
    """
    Stream the response text word by word with a delay.
    
    Args:
        role (str): The role of the speaker ("Doctor" or "Patient").
        response_text (str): The full response text to stream.
    """
    with st.chat_message(role):
        response_placeholder = st.empty()
        full_response = ""
        for word in response_text.split():
            full_response += word + " "
            response_placeholder.markdown(full_response)
            time.sleep(0.05)

def display_chat_history(agent):
    """
    Display the chat messages from the agent's memory.

    Args:
        agent (DialogueAgent): The dialogue agent object.
    """
    for message in agent.get_history():
        role, content = message.split(": ", 1)  # Split role and message content
        with st.chat_message(role):
            st.markdown(content)

def handle_user_input(agent):
    """
    Handle user input and process the conversation flow.
    
    Args:
        agent (DialogueAgent): The dialogue agent managing the conversation.
    """
    if prompt := st.chat_input("Enter your message:"):
        if st.session_state.turn == "Patient":
            # Add user message to the agent's memory
            agent.receive(prompt)
            with st.chat_message("Patient"):
                st.markdown(prompt)
            st.session_state.turn = "Doctor"  # Next turn is for the doctor

            # Generate and display doctor's response (including adding to memory)
            response = agent.generate_response()   # Generate the response
            stream_response("Doctor", response)

            st.session_state.turn = "Patient"  # Next turn is for the patient

    
def main():
    
    # Authenticate the user
    authenticator, name, authentication_status, patient_id = setup_authenticator() # To-do: Add patient ID as a parameter to the DialogueAgent class

    # Check if the user is authenticated
    if authentication_status == True:
        authenticator.logout('Logout', 'sidebar')
        st.write(f'Welcome *{name}*')

        # Initialize session state for Streamlit
        if 'agent' not in st.session_state:
            st.session_state.agent = DialogueAgent()
            st.session_state.initial_response_shown = False
            st.session_state.turn = "Doctor"  # Start with the doctor's turn
        
        agent = st.session_state.agent

        # Display chat messages from the agent's memory
        display_chat_history(agent)

        # Display initial doctor's message if not already shown
        if not st.session_state.initial_response_shown:
            initial_response = agent.generate_response()
            st.session_state.initial_response_shown = True
            st.session_state.turn = "Patient"  # After the doctor speaks, it's the patient's turn
            stream_response("Doctor", initial_response)

        # Accept user input and process the conversation flow
        handle_user_input(agent)

        # Create a button to stop the conversation
        if st.button("End Conversation", type="primary", key="end_conversation"):
            st.write("Thank you for using the RECO Consultation tool. Goodbye!")
            
            # Export the conversation history to a text file. Note this is a simple example which will need to be altered for future use.
            with open(f"../data/interim/{agent.session_id}_conversation_history.txt", "w") as file:
                for message in agent.get_history():
                    file.write(message + "\n")
  
    # Display a warning if the user is not authenticated
    elif authentication_status == False:
        st.error('Patient ID and/or Password is incorrect')
    
    # Display a warning if the user has not entered their username and password
    elif authentication_status == None:
        st.warning('Please enter your username and password')
        
if __name__ == "__main__":
    main()