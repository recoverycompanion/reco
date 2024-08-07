"""Summarizer job module.

Input: A ConversationSession ID.
What it does:
- Retrieves the conversation transcript from the database.
- Summarizes the conversation transcript using the summarizer engine.
- Saves the summary and response metadata to the database.
- Emails the summary to the HCP (look up the HCP email from db).
- Returns the summary.

Output: A summary of the conversation session, the bytes of the PDF report."""

from reco_analysis.data_model import data_models
from reco_analysis.summarizer_app import post_office, report_maker, summarizer_engine


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

    if not conversation_session.summary:
        print("Summarizing the conversation transcript.")
        # Summarize the conversation transcript
        summary, response_message = summarizer_engine.summarize(
            patient_transcript=patient_transcript,
            model=model,
        )
        # Save the summary and response metadata to the database
        conversation_session.save_summary(
            summary,
            response_message,
            session=data_models.get_session(),
        )
    else:
        print("Summary already exists in the database.")
        summary = conversation_session.transcript_summary

    # Create the PDF report -- pdf_report is a bytes object
    pdf_report = report_maker.create_patient_report(
        summary_data=summary,
        transcript=patient_transcript,
        patient_first_name=conversation_session.patient.first_name,
        patient_last_name=conversation_session.patient.last_name,
        conversation_start_time=conversation_session.created_at,
        conversation_end_time=conversation_session.messages[-1].timestamp,
        output_filename="test_report.pdf",
    )

    # Email the summary to the HCP
    patient = conversation_session.patient
    if hcp := patient.healthcare_provider:
        post_office.email_report(pdf_report, hcp, patient, conversation_session)

    return pdf_report


# test
if __name__ == "__main__":
    conversation_session_id = "f1a2dfbc-262b-4d09-a01c-62f137aca191"
    summarize_conversation(conversation_session_id)
