# Chatbot

The chatbot module implements a virtual doctor-patient conversation system using the OpenAI GPT-3 model. The chatbot is designed to simulate a medical consultation, where the virtual doctor asks questions about symptoms, medical history, and other relevant information to diagnose and recommend treatment for the patient.

Note that this directory does not include the streamlit UI app, which is located in the `chatbot_app` directory.

## Components of the Chatbot Modules

### `chatbot.py`

This module defines the core functionality of the chatbot. It includes the `DialogueAgent` class, which manages interactions between the virtual doctor and the patient.

- **DialogueAgent Class**: Manages conversation flow, tracks chat history, and generates responses using the `ChatOpenAI` model.
  - **Initialization**: Sets up the role (Doctor or Patient), system messages, and session ID.
  - **Session Management**:
    - `get_session_history`: Retrieves or initializes the chat history for a given session ID. Uses an in-memory dictionary (`session_store`) to keep track of sessions.
  - **Conversation Management**:
    - `generate_response`: Generates a response based on the conversation history.
    - `send`: Adds the AI's message to the chat history.
    - `receive`: Adds the human's message to the chat history.
    - `reset`: Clears the conversation history.
    - `get_history`: Retrieves and formats the conversation history.

### `prompts.py`

This file defines the system messages and AI guidance for different roles, providing context and structure for the chatbot's responses.

- **System Messages**:
  - `system_message_doctor`: Detailed script for the virtual doctor, including greeting, symptom inquiry, vital signs, medication review, and closing remarks.

- **AI Guidance**:
  - `ai_guidance_doctor`: Instructions for the AI acting as the doctor, focusing on continuity and avoiding repetition of questions. These instructions are provided after each run of the chat
  - `ai_guidance_patient`: Instructions for the AI acting as the patient, guiding them to respond to the doctor's questions. These instructions are provided after each run of the chat

### `test_chatbot.py`

This file contains unit tests for the chatbot components to ensure they function as expected.

- **Unit Tests**:
  - Test the initialization, response generation, message sending/receiving, and conversation history management of the `DialogueAgent`.
  - Test session management, including custom session IDs and new session initialization.