"""Summary Report Maker.

This module contains the functions to generate the summary PDF report of the
patient's conversation with the virtual doctor.

Input: A TranscriptSummary object.

Output: A PDF report summarizing the patient's overview, current symptoms, vital.
"""

import copy
import datetime
import os

from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from reco_analysis.summarizer_app import data_type

reco_analysis_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
logo_path = os.path.join(reco_analysis_path, "static", "reco_logo.jpeg")


def create_patient_report(
    summary_data: data_type.TranscriptSummary,
    transcript: list[str],
    patient_first_name: str,
    patient_last_name: str,
    conversation_start_time: datetime.datetime,
    conversation_end_time: datetime.datetime,
    output_filename: str | None = None,
) -> bytes:
    """Create a PDF report summarizing the patient's conversation with the virtual doctor.

    Args:
        summary_data (data_type.TranscriptSummary): The summary data of the patient's conversation.
        transcript (list[str]): The transcript of the patient's conversation.
        output_filename (str): The output filename for the PDF report.

    Returns:
        A file object of the PDF report.
    """
    c = canvas.Canvas(output_filename, pagesize=letter)

    logo = PILImage.open(logo_path)
    img_width, img_height = logo.size

    # Set font styles
    title_style = "Helvetica-Bold"
    section_title_style = "Helvetica-Bold"
    section_content_style = "Helvetica"

    # Draw logo and title
    title = "RECO Patient Report"
    c.setFont(title_style, 18)
    c.drawImage(logo_path, 50, 720, width=img_width / 4, height=img_height / 4)
    c.drawString(88, 727, title)
    c.line(50, 710, 550, 710)  # Draw a line under the title

    # Draw patient name and conversation date
    c.setFont(section_content_style, 11)
    c.drawString(50, 695, f"Patient: {patient_first_name}, {patient_last_name.upper()}")
    # get the duration of the conversation in 00d 00h 00m format
    hh, mm = divmod((conversation_end_time - conversation_start_time).seconds / 60, 60)
    c.drawString(
        50,
        680,
        f"Conversation Date: {conversation_start_time.strftime('%B %d, %Y %I:%M %p')} "
        f"- {conversation_end_time.strftime('%I:%M %p')} ({int(hh)}h {int(mm)}m)",
    )

    # Vertical position for content
    y_position = 665

    # Define paragraph styles
    styles = getSampleStyleSheet()
    body_style = styles["Normal"]
    body_style.fontName = "Helvetica"
    body_style.fontSize = 11
    body_style.leading = 14

    bulleted_body_style = copy.deepcopy(body_style)
    bulleted_body_style.leftIndent = 10

    def start_new_page_if_needed(new_height):
        """Check if the line will fit on the current page, if not, start a new page"""
        nonlocal y_position
        if y_position - new_height < 50:
            c.showPage()
            y_position = letter[1] - 50

    vitals_lines = "\n".join(
        [
            f"Temperature: {summary_data.vital_signs.temperature or 'N/A'} °F",
            f"Heart Rate: {summary_data.vital_signs.heart_rate or 'N/A'} bpm",
            f"Respiratory Rate: {summary_data.vital_signs.respiratory_rate or 'N/A'} bpm",
            f"Oxygen Saturation: {summary_data.vital_signs.oxygen_saturation or 'N/A'} %",
            (
                "Blood Pressure: "
                + (
                    f"{summary_data.vital_signs.blood_pressure_systolic}/{summary_data.vital_signs.blood_pressure_diastolic}"
                    if summary_data.vital_signs.blood_pressure_systolic
                    and summary_data.vital_signs.blood_pressure_diastolic
                    else "N/A"
                )
            ),
            f"Weight: {summary_data.vital_signs.weight or 'N/A'} lbs",
        ]
    )

    # Iterate through the sections and draw each section
    for key, value in [
        ("Patient Overview", summary_data.patient_overview),
        ("Current Symptoms", summary_data.current_symptoms),
        ("Vital Signs", vitals_lines),
        ("Current Medications", summary_data.current_medications),
        ("Summary", summary_data.summary),
    ]:
        value = copy.deepcopy(value)

        # Section title
        c.setFont(section_title_style, 12)
        y_position -= 20  # Move down 20 units
        c.drawString(50, y_position, key.upper())

        # Section content
        c.setFont(section_content_style, 11)
        y_position -= 20  # Move down another 20 units for content

        if isinstance(value, str):  # patient overview, summary
            summary_text = value.replace("\n", "<br/>")  # Replace newlines with HTML line breaks

            if summary_text[-1] != ".":
                summary_text = summary_text + "."

            summary_paragraph = Paragraph(summary_text, body_style)

            width, height = summary_paragraph.wrap(500, 800)
            start_new_page_if_needed(height)
            summary_paragraph.drawOn(c, 50, y_position - height + 10)
            y_position -= height  # Add extra space after the paragraph

        elif isinstance(value, list):  # current symptoms, current medications
            for line in value:
                bulleted_paragraph = Paragraph(line, bulleted_body_style, bulletText="•")
                width, height = bulleted_paragraph.wrap(500, 800)
                start_new_page_if_needed(height)
                bulleted_paragraph.drawOn(c, 50, y_position - height + 10)
                y_position -= height

    # Add the transcript to the end of the file
    c.showPage()  # Start a new page
    y_position = letter[1] - 50  # Reset y position for new page

    section_title = "Transcript"
    c.setFont(section_title_style, 12)
    y_position -= 20  # Move down 20 units
    c.drawString(50, y_position, section_title.upper())

    # Section content
    c.setFont(section_content_style, 11)
    y_position -= 20  # Move down another 20 units for content

    for transcript_line in transcript:
        # Create a paragraph with the summary text
        summary_text = transcript_line.replace("\n", "<br/>")

        if "Doctor" in summary_text[:6]:
            summary_text = "DOCTOR" + summary_text[6:]
        if "Patient" in summary_text[:7]:
            summary_text = "PATIENT" + summary_text[7:]

        summary_paragraph = Paragraph(summary_text, body_style)
        width, height = summary_paragraph.wrap(500, 800)

        start_new_page_if_needed(height)
        summary_paragraph.drawOn(c, 50, y_position - height + 10)
        y_position -= height + 10

    # Save the PDF file
    if output_filename:
        c.save()

    return c.getpdfdata()
