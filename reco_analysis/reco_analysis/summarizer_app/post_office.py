import os
import smtplib
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import make_msgid

from dotenv import load_dotenv

from reco_analysis.data_model import data_models

load_dotenv()

body_template = """Hi {hcp_first_name},\n
Please find attached the RECO patient report for {patient_name}, for a conversation on {session_date_stylized_with_time}.\n
If intervention is needed, you can reach out to the patient at {patient_email}\n
-- RECO"""


def email_report(
    pdf_bytes: bytes,
    hcp: data_models.HealthcareProvider,
    patient: data_models.Patient,
    conversation_session: data_models.ConversationSession,
) -> bool:
    """Send an email with a PDF report as an attachment.

    Args:
        pdf_bytes (bytes): The bytes of the PDF report.
        hcp_email (str): Email address of the healthcare provider.
        patient_name (str): Name of the patient for contextual email content.

    Returns:
        bool: True if the email was sent successfully.
    """
    # Email setup
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
        raise ValueError("SMTP server details are missing in the environment variables.")

    # Email content
    patient_name = patient.first_name + " " + str(patient.last_name).upper()
    session_date = conversation_session.created_at
    session_date_stylized = session_date.strftime("%B %d, %Y")
    session_date_stylized_with_time = session_date.strftime("%B %d, %Y, %I:%M %p")
    session_date_numbers_only = session_date.strftime("%Y-%m-%d %H:%M:%S")
    subject = f"RECO Patient Report: {patient_name}, {session_date_stylized}"
    body = body_template.format(
        hcp_first_name=hcp.first_name,
        patient_name=patient_name,
        session_date_stylized_with_time=session_date_stylized_with_time,
        patient_email=patient.email,
    )

    # Create the email message
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = Address(display_name="RECO", addr_spec=smtp_user)
    msg["To"] = hcp.email
    msg.set_content(body)

    # Attach the PDF report
    as_cid = make_msgid()
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=f"RECO summary - {patient_name} - {session_date_numbers_only}.pdf",
        cid=as_cid[1:-1],
    )

    breakpoint()  # throttling this for now, don't want to spam while testing

    # Send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Secure the connection
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        print("Email sent successfully!")

    return True
