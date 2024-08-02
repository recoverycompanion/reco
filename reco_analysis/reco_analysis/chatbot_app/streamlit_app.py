import time
import typing
from pathlib import Path
from typing import TypedDict

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

from reco_analysis.chatbot.chatbot import DialogueAgent
from reco_analysis.data_model import data_models
from reco_analysis.summarizer_app import summarizer_job

session = data_models.get_session()


class CredentialsType(TypedDict):
    credentials: dict[str, typing.Any]
    cookie: dict[str, str]
    pre_authorized: str


def load_credentials(file_path) -> CredentialsType:
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


def setup_authenticator() -> (
    typing.Tuple[stauth.Authenticate, str, bool | None, str, data_models.Patient | None]
):
    """
    Set up the authenticator for the Streamlit application.

    Returns:
        tuple: A tuple containing the authenticator object, the user's name, the authentication status, and the username (i.e., the patient ID)
    """
    # Load credentials from the YAML file
    credentials_path = Path(__file__).parent / "credentials.yaml"
    credentials_yml = load_credentials(credentials_path)

    # load the credentials from postgresql db
    usernames = {}
    all_patients = data_models.Patient.get_all_patients(session)
    for patient in all_patients:
        usernames[patient.username] = {
            "email": patient.email,
            "patient_id": patient.id,
            "failed_login_attempts": 0,  # TODO: consider tracking failed login attempts
            "logged_in": False,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "name": patient.first_name + " " + patient.last_name,
            "password": patient.password,
        }

    # Create an authentication object
    authenticator = stauth.Authenticate(
        credentials={"usernames": usernames},
        cookie_name=credentials_yml["cookie"]["name"],
        cookie_key=credentials_yml["cookie"]["key"],
        cookie_expiry_days=credentials_yml["cookie"]["expiry_days"],
        pre_authorized=credentials_yml.get("pre_authorized", None),
    )

    name, authentication_status, patient_username = authenticator.login(
        location="main",
        fields={
            "Form name": "Login",
            "Username": "Patient Username",
            "Password": "Password",
            "Login": "Login",
        },
    )

    # from patient_username, get the Patient object
    patient = (
        session.query(data_models.Patient)
        .filter(data_models.Patient.username == patient_username)
        .first()
    )

    return authenticator, name, authentication_status, patient_username, patient


def sign_up_new_patient():
    """
    Sign up a new patient by entering the required information.

    Returns:
        None
    """
    st.write("Sign up as a new patient by entering the following information:")
    username = st.text_input("Username")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    st.write(
        "**Disclaimer**: RECO is a research project and not a real medical service, "
        "and because it's based on Generative AI, it can sometimes provide incorrect "
        "or harmful information."
        "Any advice given by the chatbot is not a substitute for professional medical advice. "
        "Please do not enter any sensitive personal information. As the data you enter may be used for research purposes. "
        "If you have a medical emergency, please call 911.\n\n"
        "By signing up, you understand and agree to these terms."
    )

    error_placeholder = st.empty()
    if st.button("Sign up"):
        if not all([username, first_name, last_name, email, password]):
            error_placeholder.error("Please fill out all fields")
        else:
            try:
                new_patient = data_models.Patient.new_patient(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password=password,
                    session=session,
                )
                error_placeholder.success(
                    f"New patient account created for {new_patient.first_name} with username {new_patient.username}!"
                )
            except ValueError as e:
                # likely a duplicate username
                error_placeholder.error(f"Error: {e.args[0]}")


def initialize_agent(patient: data_models.Patient) -> DialogueAgent:
    """
    Initialize the DialogueAgent for the given patient.

    Args:
        patient (data_models.Patient): The patient object.

    Returns:
        DialogueAgent: The initialized DialogueAgent object.
    """
    latest_conversation = patient.get_latest_conversation_session()
    session_id = (
        None
        if latest_conversation is None or latest_conversation.completed
        else latest_conversation.id
    )
    agent = DialogueAgent(
        role="Doctor",
        patient_id=patient.id,
        session_id=session_id,
    )
    latest_message_role = agent.get_latest_message_role()
    st.session_state.turn = (
        "Doctor" if latest_message_role is None or latest_message_role == "Patient" else "Patient"
    )
    st.session_state.conversation_ended = False
    return agent


def get_icon(role: str) -> str:
    """
    Get the icon for the speaker based on their role.

    Args:
        role (str): The role of the speaker ("Doctor" or "Patient").

    Returns:
        str: The icon for the speaker.
    """
    return "ai" if role == "Doctor" else "user"


def stream_response(role: str, response_text: str):
    """
    Stream the response text line by line with a delay, respecting newlines in the text.

    Args:
        role (str): The role of the speaker ("Doctor" or "Patient").
        response_text (str): The full response text to stream.
    """
    with st.chat_message(role, avatar=get_icon(role)):
        response_placeholder = st.empty()
        full_response = ""
        
        for line in response_text.splitlines():  # Split the text by lines first
            if line.strip():  # Process non-empty lines
                words = line.split()
                for word in words:
                    full_response += word + " "
                    response_placeholder.markdown(full_response)
                    time.sleep(0.05)
                full_response += "\n"  # Add newline after each processed line
            else:
                full_response += "\n"  # Preserve blank lines
                response_placeholder.markdown(full_response)
                time.sleep(0.05)
        
        # Ensure the final output respects the original formatting
        response_placeholder.markdown(full_response)


def display_chat_history(agent: DialogueAgent):
    """
    Display the chat messages from the agent's memory.

    Args:
        agent (DialogueAgent): The dialogue agent object.
    """
    for message in agent.memory.messages:
        role, content = message.name, message.content
        with st.chat_message(role, avatar=get_icon(role)):
            st.markdown(content)


def handle_user_input(agent: DialogueAgent, prompt: str | None):
    """
    Handle user input and process the conversation flow.

    Args:
        agent (DialogueAgent): The dialogue agent managing the conversation.
        prompt (str | None): The output from streamlit chat_input component.
    """
    if prompt:
        # Add user message to the agent's memory and adjust's the agent's con
        agent.receive(prompt)
        with st.chat_message("Patient", avatar=get_icon("Patient")):
            st.markdown(prompt)
        st.session_state.turn = "Doctor"  # Next turn is for the doctor

        # Generate and display doctor's response (including adding to memory)
        response = agent.generate_response()  # Generate the response
        stream_response("Doctor", response)
        st.session_state.turn = "Patient"  # Next turn is for the patient


def end_conversation(agent: DialogueAgent, session):
    """
    Ends the conversation and marks the session as completed.

    Args:
        agent (DialogueAgent): The dialogue agent managing the conversation.
        session (Session): The SQLAlchemy session object.
    """
    st.session_state.conversation_ended = True
    agent.end_conversation = True
    convo_session: data_models.ConversationSession = data_models.ConversationSession.get_by_id(
        agent.session_id, session
    )
    convo_session.mark_as_completed(session)

    # also generate a summary email
    summarizer_job.summarize_conversation(conversation_session_id=convo_session.id)


def reset_chat():
    """
    Reset the chat by clearing the session state and deleting the agent.

    Returns:
        None
    """
    del st.session_state.agent
    st.session_state.conversation_ended = False
    st.empty()
    st.rerun()


def export_conversation_history(agent):
    """
    Export the conversation history to a text file for further analysis.

    Args:
        agent (DialogueAgent): The dialogue agent object.
    """
    conversation_history_dir = Path(__file__).parent.parent.parent / "data/streamlit_transcripts"
    with open(
        f"{conversation_history_dir}/{agent.session_id}_conversation_history.txt", "w"
    ) as file:
        for message in agent.get_history():
            file.write(message + "\n")

def main():
    """
    Main function to set up and run the Streamlit interface for the chatbot,
    handling the interaction flow and session state.
    """
    # Set the page title
    st.set_page_config(page_title="RECO Consultation Tool", page_icon=":hearts:")

    # Display the title and description
    with st.sidebar:
        st.title("RECO: Recovery Companion")
        st.markdown(
            "Welcome to the RECO Consultation Tool! I am here to help you with your recovery journey."
        )

    # Authenticate the user
    if (
        "authentication_status" not in st.session_state
        or not st.session_state.authentication_status
    ):
        authenticator, _, _, _, patient = setup_authenticator()
        st.session_state.authentication_details = (authenticator, patient)
    else:
        authenticator, patient = st.session_state.authentication_details

    # Check if the user is authenticated
    if st.session_state.authentication_status == True and patient is not None:
        authenticator.logout("Logout", "sidebar")
        st.write(f"Welcome *{patient.first_name}*")

        # Initialize session state for Streamlit
        if "agent" not in st.session_state:
            st.session_state.agent = initialize_agent(patient)

        agent: DialogueAgent = st.session_state.agent

        # Display chat messages from the agent's memory
        display_chat_history(agent)

        # Create a button to stop the conversation
        conversation_flow_button = st.sidebar.empty()

        # Allow the user to end the conversation
        if conversation_flow_button.button(
            "End Conversation",
            type="primary",
            key="end_conversation",
            disabled=st.session_state.conversation_ended,
        ):
            end_conversation(agent, session)

        # Display initial doctor's message if not already shown
        if st.session_state.turn == "Doctor":
            initial_response = agent.generate_response()
            # Remove the initial message from the memory to avoid duplication
            agent.memory.messages.pop()
            st.session_state.turn = "Patient"  # After the doctor speaks, it's the patient's turn
            stream_response("Doctor", initial_response)

        # Accept user input and process the conversation flow
        if not st.session_state.conversation_ended:
            prompt = st.chat_input(
                "Enter your message:", disabled=st.session_state.conversation_ended
            )
            handle_user_input(agent, prompt)

        # End the conversation if the patient confirms or conversation_flow_button is clicked
        else:
            st.write("Thank you for using the RECO Consultation tool. Goodbye")
            if conversation_flow_button.button(
                "New Conversation", key="new_conversation", type="secondary"
            ):
                reset_chat()

    else:
        # Display a warning if the user is not authenticated
        if st.session_state.authentication_status == False:
            st.error("Patient ID and/or Password is incorrect")

        # allow for new patient account sign up
        with st.popover("Sign up as a new patient"):
            sign_up_new_patient()


if __name__ == "__main__":
    main()
