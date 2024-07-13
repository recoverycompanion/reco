import datetime
import os

import pytest

from reco_analysis.summarizer_app import data_type, report_maker

test_module_path = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture
def summary_data():
    return data_type.TranscriptSummary(
        patient_overview="Patient is a something",
        current_symptoms=["Patient has a cough", "Patient has a fever", "long symptom " * 10],
        vital_signs=data_type.VitalSigns(
            temperature=98.6,
            heart_rate=72,
            respiratory_rate=18,
            oxygen_saturation=98,
            blood_pressure_systolic=120,
            blood_pressure_diastolic=80,
            weight=150,
        ),
        current_medications=["Tylenol", "Cough syrup", "Antibiotics"],
        summary="Patient has a cold " * 20,
    )


@pytest.fixture
def fake_transcript():
    return (
        ["Doctor: " + f"Hello, how are you feeling today? " * 3]
        + ["Patient: " + f"I'm feeling great."]
    ) * 30


def test_report_maker(summary_data, fake_transcript):
    ret = report_maker.create_patient_report(
        summary_data,
        fake_transcript,
        patient_first_name="John",
        patient_last_name="Doe",
        conversation_start_time=datetime.datetime.now() - datetime.timedelta(minutes=70),
        conversation_end_time=datetime.datetime.now(),
        output_filename=test_module_path + "/test_report.pdf",
    )
