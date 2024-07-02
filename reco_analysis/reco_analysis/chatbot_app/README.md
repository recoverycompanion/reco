## Components of the Chatbot Modules

### `credentials.yaml`

This file contains user credentials and cookie settings for authentication in the RECO Consultation chatbot.

- **Credentials**: Stores usernames, emails, login status, names, and passwords for users.
- **Cookie Settings**: Defines the expiry days, key, and name for session cookies.

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
    
- **Usage**: Run the app with the command:
  ```sh
  streamlit run streamlit_app.py
  ```