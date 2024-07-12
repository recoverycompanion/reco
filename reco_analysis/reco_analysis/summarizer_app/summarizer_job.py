"""Summarizer job module.

Input: A ConversationSession ID.
What it does:
- Retrieves the conversation transcript from the database.
- Summarizes the conversation transcript using the summarizer engine.
- Saves the summary and response metadata to the database.
- Emails the summary to the HCP (look up the HCP email from db).
- Returns the summary.

Output: A summary of the conversation session, the bytes of the PDF report."""

import os
import typing

from reco_analysis.data_model import data_models
from reco_analysis.summarizer_app import report_maker, summarizer_engine


def summarize_conversation(
    conversation_session_id: str,
    model: summarizer_engine.ChatOpenAI = summarizer_engine.default_model,
) -> bytes:
    """Summarizes a conversation session.

    Args:
        conversation_session_id (str): The ID of the conversation session.

    Returns:
        bytes: The bytes of the PDF report.
    """
    # Retrieve the conversation transcript from the database
    conversation_session = data_models.ConversationSession.get_by_id(
        conversation_session_id, session=data_models.get_session()
    )

    if not conversation_session.completed:
        raise ValueError("The conversation session is not completed.")

    patient_transcript = conversation_session.get_transcript()

    if not patient_transcript:
        raise ValueError("No transcript found for the conversation session.")

    # Summarize the conversation transcript
    summary, response_message = summarizer_engine.summarize(
        patient_transcript=patient_transcript,
        model=model,
    )

    # Create the PDF report
    pdf_report = report_maker.create_patient_report(
        summary_data=summary,
        transcript=patient_transcript,
    )

    # Save the summary and response metadata to the database
    conversation_session.save_summary(summary, response_message)

    # TODO: Email the summary to the HCP

    return pdf_report


# test
if __name__ == "__main__":
    conversation_session_id = "fda7e5bb-7a4f-4f8d-a822-4cd520064243"
    summarize_conversation(conversation_session_id)
