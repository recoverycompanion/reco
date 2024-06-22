import os
import streamlit as st
from dotenv import load_dotenv
from reco_analysis.chatbot.chatbot import DialogueAgent
from langchain_openai import ChatOpenAI
import time

import os
import streamlit as st
from dotenv import load_dotenv  # Ensure to load environment variables if needed
from reco_analysis.chatbot.chatbot import DialogueAgent
from langchain_openai import ChatOpenAI
import time

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

def main():
    st.title("RECO Consultation")

    # Initialize session state for Streamlit
    if 'agent' not in st.session_state:
        st.session_state.agent = DialogueAgent()
        st.session_state.initial_response_shown = False
        st.session_state.turn = "Doctor"  # Start with the doctor's turn
    
    agent = st.session_state.agent

    # Display chat messages from the agent's memory
    for message in agent.get_history():
        role, content = message.split(": ", 1)  # Split role and message content
        with st.chat_message(role):
            st.markdown(content)

    # Display initial doctor's message if not already shown
    if not st.session_state.initial_response_shown:
        initial_response = agent.generate_response()
        st.session_state.initial_response_shown = True
        st.session_state.turn = "Patient"  # After the doctor speaks, it's the patient's turn
        stream_response("Doctor", initial_response)

    # Accept user input and process the conversation flow
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

    # Create a button to stop the conversation
    if st.button("End Conversation", type="primary", key="end_conversation"):
        st.write("Thank you for using the RECO Consultation tool. Goodbye!")
        
        # Export the conversation history to a text file. Note this is a simple example which will need to be altered for future use.
        with open(f"../data/interim/{agent.session_id}_conversation_history.txt", "w") as file:
            for message in agent.get_history():
                file.write(message + "\n")

if __name__ == "__main__":
    main()