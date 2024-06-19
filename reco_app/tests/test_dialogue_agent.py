"""Test dialogue agent."""

from langchain_openai import ChatOpenAI

from reco_app.backend import prompts
from reco_app.backend.dialogue_agent import DialogueAgent, UserInterface


def _test_dialogue_agent(system_message, agent_role, user_messages, verbose=False):
    """
    Tests the DialogueAgent acting as a doctor/patient with a series of patient/doctor messages.
    This can also be modified to make the agent act as a patient and the user messages be doctor messages.

    Args:
        system_message (str): The initial system message for the agent
        agent_role (str): The role of the agent (either 'doctor' or 'patient')
        user_messages (List[str]): The list of user messages to simulate the conversation
        verbose (bool, optional): Whether to print verbose output. Defaults to False.
    """
    # Set up the OpenAI model
    model = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo")

    # Create the DialogueAgent instance for the doctor
    agent = DialogueAgent(
        role=agent_role, system_message=system_message, model=model, verbose=verbose
    )

    # Define user and agent roles
    agent_role = agent_role.capitalize()
    user_role = "Patient" if agent_role == "Doctor" else "Doctor"

    # Reset the conversation
    agent.reset()

    # Simulate the conversation
    for msg in user_messages:
        # Doctor receives the patient's message
        agent.receive(message=msg)

        # Doctor sends a response
        response = agent.generate_response()

        # Print the response
        print(f"{user_role}: {msg}")
        print(f"{agent_role}: {response}\n")

    # Get the full conversation history
    history = agent.get_history()

    return history


# Integration and testing function
def _test_dialogue_with_ui(system_message, agent_role, verbose=False):
    """
    This function simulates a conversation between a virtual doctor and a patient using a user interface, whereby the user can input messages acting as the patient or the doctor.
    This can also be modified to simulate a conversation whereby the agent acts as the patient and the user acts as the doctor.

    Args:
        system_message (str): The initial system message for the agent
        agent_role (str): The role of the agent (either 'doctor' or 'patient')
    """
    # Set up the OpenAI model
    model = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo")

    # Create the DialogueAgent instance for the doctor
    agent = DialogueAgent(
        role=agent_role, system_message=system_message, model=model, verbose=verbose
    )

    # Define user and agent roles
    agent_role = agent_role.capitalize()
    human_role = "Patient" if agent_role == "Doctor" else "Doctor"

    # Create the UserInterface instance
    ui = UserInterface(agent_role=agent_role)

    # Simulate the interaction
    while True:
        # Collect user input
        user_input = ui.collect_user_input()
        print(f"{human_role}: {user_input}")

        if user_input.lower() == "exit":
            break  # Exit if in simulation mode or if input is None

        # Doctor agent receives the user's message
        agent.receive(message=user_input)

        # Doctor agent sends a response
        response = agent.generate_response()

        # Display the doctor's response
        ui.display_response(response)

    # Get the full conversation history
    history = agent.get_history()

    return history


class TestDialogueAgent:
    def test_dialogue_agent_patient(self):
        # Run the test function with the agent acting as a doctor
        _test_dialogue_agent(
            system_message=prompts.SYSTEM_MESSAGE_DOCTOR,
            agent_role="Doctor",
            user_messages=[
                "Hello, doctor. I've been feeling a bit dizzy lately.",
                "I've also been experiencing some chest pain and shortness of breath.",
                "I'm worried it might be related to my heart condition.",
            ],
        )

    def test_dialogue_agent_doctor(self):
        _test_dialogue_agent(
            system_message=prompts.SYSTEM_MESSAGE_PATIENT,
            agent_role="patient",
            user_messages=[
                "Hi there. How are you doing today?",
                "What symptoms are you currently experiencing?",
                "Have you been taking your medications regularly?",
            ],
        )

    def test_dialogue_with_ui_patient(self):
        _test_dialogue_with_ui(
            system_message=prompts.SYSTEM_MESSAGE_DOCTOR, agent_role="Doctor"
        )

    def test_dialogue_with_ui_doctor(self):
        _test_dialogue_with_ui(
            system_message=prompts.SYSTEM_MESSAGE_PATIENT, agent_role="Patient"
        )
