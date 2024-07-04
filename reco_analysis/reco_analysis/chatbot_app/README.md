# Chatbot App

This is the Streamlit application for the RECO Consultation chatbot, which serves up
an interactive chat interface for users to converse with a virtual doctor.

## Components of the Chatbot App Module

### `credentials.yaml`

This file contains cookie settings for authentication in the RECO Consultation chatbot. Cookie settings include the expiry days, key, and name for session cookies.

### `streamlit_app.py`

This module defines and runs the Streamlit application for the RECO Consultation chatbot. It simulates a conversation between a virtual doctor and a patient.

- **Authentication**: Loads user credentials and sets up authentication.
- **Chat Interface**: Manages the dialogue flow using the `DialogueAgent` class.
  - **Functions**:
    - `load_credentials`: Loads credentials from a YAML file.
    - `setup_authenticator`: Configures the authenticator for the app.
    - `get_icon`: Determines the icon for the speaker based on their role.
    - `stream_response`: Streams response text with a typing effect.
    - `display_chat_history`: Displays the conversation history.
    - `handle_user_input`: Handles user input and processes the conversation flow.
    - `main`: Sets up and runs the Streamlit app, handling interaction flow and session state.

- **Pre-requisites**: Ensure that the postgres database is running and up-to-date. Please refer to [data_model/README.md](../data_model/README.md) for more information on database setup.

- **Usage**: Run the app with the command from this directory:

  ```sh
  streamlit run streamlit_app.py
  ```
