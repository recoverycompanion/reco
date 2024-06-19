"""Dialogue Simulator

The DialogueSimulator class simulates a conversation flow between two agents (a doctor and a patient). It does so by managing the turn-taking process and message exchanges between agents.

Key features:

Initialization: Takes a list of DialogueAgent instances and prepares the simulator for running conversations.
Turn Selection: Determines which agent speaks next based on a simple turn-taking mechanism.
This class is essential for running automated tests and simulations of conversations between different agents.
"""

import typing

from reco_app.backend.dialogue_agent import DialogueAgent


class DialogueSimulator:
    def __init__(self, agents: typing.List[DialogueAgent]):
        """
        Initialize the DialogueSimulator with a list of agents and the starting agent.

        Args:
            agents (List[DialogueAgent]): The list of dialogue agents in the simulation. Must contain exactly 2 agents (a doctor and a patient).
        """

        # Check if the number of agents is exactly 2
        self.agents = agents
        if len(self.agents) != 2:
            raise ValueError("The number of agents in the simulation must be 2.")

        # Define the doctor and patient agents
        self.doctor_idx, self.patient_idx = self.define_doctor_and_patient_indices()
        self.doctor_agent = self.agents[self.doctor_idx]
        self.patient_agent = self.agents[self.patient_idx]

    def define_doctor_and_patient_indices(self) -> typing.Tuple[int, int]:
        """
        Define the doctor and patient indices from the list of agents.
        """
        for i, agent in enumerate(self.agents):
            if agent.role == "Doctor":
                doctor_idx = i
            elif agent.role == "Patient":
                patient_idx = i
        return doctor_idx, patient_idx

    def switch_agents(self) -> None:
        """
        Switch the current agent between the doctor and the patient.
        """
        self.current_agent = (
            self.doctor_agent
            if self.current_agent == self.patient_agent
            else self.patient_agent
        )

    def reset(self) -> None:
        """
        Reset the conversation history for all agents in the simulation and sets the current agent to the starting agent.
        """
        for agent in self.agents:
            agent.reset()
        self.current_agent = (
            self.doctor_agent if self.starting_agent == "Doctor" else self.patient_agent
        )

    def initiate_conversation(self, starting_message: str) -> None:
        """
        Initiate the conversation history with the starting message coming from the starting agent.
        """
        self.reset()

        speaker = (
            self.doctor_agent if self.starting_agent == "Doctor" else self.patient_agent
        )
        receiver = (
            self.patient_agent if self.starting_agent == "Doctor" else self.doctor_agent
        )

        speaker.send(starting_message)
        receiver.receive(starting_message)

        self.switch_agents()

    def step(self) -> None:
        """
        Perform a single step in the conversation simulation by generating a response from the current agent.
        """
        # Define the speaker and receiver
        speaker = self.current_agent
        receiver = (
            self.doctor_agent if speaker == self.patient_agent else self.patient_agent
        )

        # Generate a response from the speaker
        message = speaker.generate_response()
        print(f"{speaker.role}: {message}")

        # Receive the response from the speaker
        receiver.receive(message)

        # Switch the current agent
        self.switch_agents()

    def run(
        self, num_steps: int, starting_agent: str, starting_message: str
    ) -> typing.List[str]:
        """
        Run the conversation simulation for a given number of steps.

        Args:
            num_steps (int): The number of steps to run the simulation.
            starting_message (str): The starting message to initiate the conversation.
        """
        # Set the current agent to the starting agent
        self.starting_agent = starting_agent.capitalize()
        if self.starting_agent not in ["Doctor", "Patient"]:
            raise ValueError("Starting agent must be either 'Doctor' or 'Patient'")
        self.current_agent = (
            self.doctor_agent if self.starting_agent == "Doctor" else self.patient_agent
        )

        # Inject the initial message into the memory of the conversation
        self.initiate_conversation(starting_message)

        # Run the simulation for the specified number of steps
        for _ in range(num_steps):
            self.step()

        # Get history from the starting agent
        history = (
            self.doctor_agent.get_history()
            if self.starting_agent == "Doctor"
            else self.patient_agent.get_history()
        )

        return history
