from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.schema import BaseChatMessageHistory

def get_session_history(session_id: str, session_store: dict) -> BaseChatMessageHistory:
    """
    Store the chat history for a given session ID.
    
    Args:
        session_id (str): The session ID to retrieve the chat history for.
        session_store (dict): The dictionary to store the chat histories.
    
    Returns:
        BaseChatMessageHistory: The chat history for the session.
    """
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]