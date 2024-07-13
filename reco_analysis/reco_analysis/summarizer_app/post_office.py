import os
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid

from dotenv import load_dotenv

from reco_analysis.data_model import data_models

load_dotenv()


def email_report(
    pdf_bytes: bytes, hcp: data_models.HealthcareProvider, patient: data_models.Patient
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
    subject = f"Medical Summary for {patient_name}"
    body = f"Please find attached the medical summary for {patient_name}."

    # Create the email message
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = hcp.email
    msg.set_content(body)

    # Attach the PDF report
    as_cid = make_msgid()
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=f"{patient_name}_Summary.pdf",
        cid=as_cid[1:-1],
    )

    # Send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Secure the connection
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        print("Email sent successfully!")

    return True
