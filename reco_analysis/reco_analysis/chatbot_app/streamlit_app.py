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
    session_id = None if latest_conversation is None or latest_conversation.completed else latest_conversation.id
    agent = DialogueAgent(
        role="Doctor",
        patient_id=patient.id,
        session_id=session_id,
    )
    latest_message_role = agent.get_latest_message_role()
    st.session_state.turn = "Doctor" if latest_message_role is None or latest_message_role == "Patient" else "Patient"
    st.session_state.conversation_ended = False
    return agent


def get_icon(role):
    """
    Get the icon for the speaker based on their role.

    Args:
        role (str): The role of the speaker ("Doctor" or "Patient").

    Returns:
        str: The icon for the speaker.
    """
    return "ai" if role == "Doctor" else "user"


def stream_response(role, response_text):
    """
    Stream the response text word by word with a delay.

    Args:
        role (str): The role of the speaker ("Doctor" or "Patient").
        response_text (str): The full response text to stream.
    """
    with st.chat_message(role, avatar=get_icon(role)):
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
    for message in agent.memory.messages:
        role, content = message.name, message.content
        with st.chat_message(role, avatar=get_icon(role)):
            st.markdown(content)


def handle_user_input(agent, prompt: str | None):
    """
    Handle user input and process the conversation flow.

    Args:
        agent (DialogueAgent): The dialogue agent managing the conversation.
        prompt (str | None): The output from streamlit chat_input component.
    """
    if prompt:
        if st.session_state.turn == "Patient":
            # Add user message to the agent's memory and adjust's the agent's con
            agent.receive(prompt)
            st.write(f"Debug messages: {agent.memory.messages}")
            st.write(f"Debug last doctor and patient message: {agent.get_last_doctor_patient_messages()}")
            st.write(f"Debug conversation end: {agent.end_conversation}")
            with st.chat_message("Patient", avatar=get_icon("Patient")):
                st.markdown(prompt)
            st.session_state.turn = "Doctor"  # Next turn is for the doctor

            # Check if a conversation end is detected and confirm
            if agent.end_conversation:
                confirm_conversation_end(agent)
            else:
                # Generate and display doctor's response (including adding to memory)
                response = agent.generate_response()  # Generate the response
                stream_response("Doctor", response)

            st.session_state.turn = "Patient"  # Next turn is for the patient


def confirm_conversation_end(agent):
    """
    Confirms whether the patient wants to end the conversation or continue.

    Args:
        agent (DialogueAgent): The dialogue agent managing the conversation.
    """
    # Have the agent send a message confirming whether the patient wants to end the conversation
    message = "It looks like this conversation is coming to a close. Would you like to end the conversation?"
    agent.send(message)
    stream_response("Doctor", message)

    # Create a container for the buttons
    # TODO: MAKE SURE CHAT IS DISABLED AFTER CLICKING YES
    with st.container():
        if st.button("Yes"):
            agent.receive("Yes")
            end_conversation(agent, session)

        if st.button("No"):
            agent.receive("No")
            agent.end_conversation = False
            st.session_state.conversation_ended = False

            # Generate and display doctor's response (including adding to memory)
            response = agent.generate_response()
            stream_response("Doctor", response)
            st.session_state.turn = "Patient"


def end_conversation(agent: DialogueAgent, session):
    """
    Ends the conversation and marks the session as completed.

    Args:
        agent (DialogueAgent): The dialogue agent managing the conversation.
        session (Session): The SQLAlchemy session object.
    """
    st.session_state.conversation_ended = True
    convo_session: data_models.ConversationSession = (
        data_models.ConversationSession.get_by_id(agent.session_id, session)
    )
    convo_session.mark_as_completed(session)
    st.write("Thank you for using the RECO Consultation tool. Goodbye!")


def reset_chat():
    """
    Reset the chat by clearing the session state and deleting the agent.

    Returns:
        None
    """
    del st.session_state.agent
    st.session_state.conversation_ended = False
    st.empty()


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
    authenticator, name, authentication_status, patient_username, patient = setup_authenticator()

    # Check if the user is authenticated
    if authentication_status == True and patient is not None:
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

        # Display initial doctor's message if not already shown
        if st.session_state.turn == "Doctor":
            initial_response = agent.generate_response()
            st.session_state.turn = "Patient"  # After the doctor speaks, it's the patient's turn
            stream_response("Doctor", initial_response)

        # Accept user input and process the conversation flow
        if not st.session_state.conversation_ended:
            prompt = st.chat_input(
                "Enter your message:", disabled=st.session_state.conversation_ended
            )
            handle_user_input(agent, prompt)
            if conversation_flow_button.button(
                "End Conversation",
                type="primary",
                key="end_conversation",
                disabled=st.session_state.conversation_ended,
            ):
                end_conversation(agent, session)

        elif conversation_flow_button.button(
                "New Conversation", key="new_conversation", type="secondary"
            ):
                reset_chat()
    else:
        # Display a warning if the user is not authenticated
        if authentication_status == False:
            st.error("Patient ID and/or Password is incorrect")

        # allow for new patient account sign up
        with st.popover("Sign up as a new patient"):
            sign_up_new_patient()


if __name__ == "__main__":
    main()