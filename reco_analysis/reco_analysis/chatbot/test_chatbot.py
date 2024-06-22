import unittest
from typing import List, Tuple, Dict, Any
from unittest.mock import MagicMock
from langchain.schema import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from reco_analysis.chatbot.chatbot import DialogueAgent
from reco_analysis.chatbot.session_management import get_session_history
import uuid

# Mock the ChatOpenAI model
mock_model = MagicMock(spec=ChatOpenAI)
mock_model.invoke.return_value = "Mocked response"

session_store = {}

# Unit tests for the DialogueAgent
class DialogueAgentTests(unittest.TestCase):

    def setUp(self):
        """
        Set up a fresh DialogueAgent instance before each test.
        """
        global session_store
        session_store.clear()
        self.agent = DialogueAgent(
            role='Doctor',
            system_message="You are a virtual doctor.",
            model=mock_model,
            session_id=None
        )

    def test_initialization(self):
        """
        Test that the DialogueAgent initializes correctly.
        """
        self.assertEqual(self.agent.role, 'Doctor')
        self.assertEqual(self.agent.human_role, 'Patient')
        self.assertEqual(self.agent.system_message, "You are a virtual doctor.")
        self.assertTrue(isinstance(uuid.UUID(self.agent.session_id), uuid.UUID))
        self.assertEqual(self.agent.memory.messages, [])

    def test_reset(self):
        """
        Test that resetting the memory clears the conversation history.
        """
        # Add some messages to the memory
        self.agent.memory.add_message(HumanMessage(content="Test message", name="Patient"))
        self.assertGreater(len(self.agent.memory.messages), 0)

        # Reset the memory
        self.agent.reset()
        self.assertEqual(len(self.agent.memory.messages), 0)

    def test_generate_response(self):
        """
        Test that the generate_response method generates a response.
        """
        response = self.agent.generate_response()
        self.assertEqual(response, "Mocked response")
        self.assertGreater(len(self.agent.memory.messages), 0)

    def test_send(self):
        """
        Test that sending a message adds it to the conversation history.
        """
        self.agent.send("Test AI message")
        last_message = self.agent.memory.messages[-1]
        self.assertEqual(last_message.content, "Test AI message")
        self.assertEqual(last_message.name, "Doctor")

    def test_receive(self):
        """
        Test that receiving a message adds it to the conversation history.
        """
        self.agent.receive("Test human message")
        last_message = self.agent.memory.messages[-1]
        self.assertEqual(last_message.content, "Test human message")
        self.assertEqual(last_message.name, "Patient")

    def test_get_history(self):
        """
        Test that the get_history method retrieves the conversation history.
        """
        self.agent.receive("First message")
        self.agent.send("Second message")
        history = self.agent.get_history()
        self.assertEqual(history[0], "Patient: First message")
        self.assertEqual(history[1], "Doctor: Second message")

# Additional tests focused on session ID management and session history.
class TestSessionManagement(unittest.TestCase):
    def setUp(self):
        # Ensure the session store is clear before each test
        global session_store
        session_store.clear()

    def test_custom_session_id(self):
        """
        Test that conversation history is resumed with a custom session ID.
        """
        agent = DialogueAgent(
            role='Doctor',
            system_message="You are a virtual doctor.",
            model=mock_model,
            session_id="custom-session-id"
        )
        self.assertEqual(agent.session_id, "custom-session-id")

        # Add some messages to the memory
        agent.memory.add_message(HumanMessage(content="Test message", name="Patient"))
        self.assertEqual(len(agent.memory.messages), 1)

        # Create a new agent with the same session ID
        agent2 = DialogueAgent(
            role='Doctor',
            system_message="You are a virtual doctor.",
            model=mock_model,
            session_id="custom-session-id"
        )
        self.assertEqual(agent2.session_id, "custom-session-id")

        # Check that the conversation history is resumed
        self.assertEqual(len(agent2.memory.messages), 1)
        self.assertEqual(agent2.memory.messages[0].content, "Test message")

    def test_new_session_id(self):
        """
        Test that a new session ID starts with an empty history.
        """
        agent = DialogueAgent(
            role='Doctor',
            system_message="You are a virtual doctor.",
            model=mock_model,
            session_id="new-session-id"
        )
        self.assertEqual(agent.session_id, "new-session-id")
        self.assertEqual(len(agent.memory.messages), 0)

if __name__ == '__main__':
    unittest.main(argv=[''], exit=False)