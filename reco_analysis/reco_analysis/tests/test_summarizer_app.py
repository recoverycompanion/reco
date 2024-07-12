import json
import os
import random

import dotenv
import pytest

from reco_analysis.summarizer_app import summarizer_engine

env_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
dotenv.load_dotenv(env_file_path)

fake_patient_name = "John"
test_transcript = [
    f"Doctor: Hello {fake_patient_name}, how are you feeling today after your discharge?",
    "Patient: I've been short of breath when walking around the house.",
    "Doctor: Does this occur when you're at rest or climbing stairs?",
    "Patient: It's worse when climbing stairs but not at rest.",
    "Doctor: Any nighttime shortness of breath?",
    "Patient: No, that hasn't happened.",
    "Doctor: How about sleeping? Are you using more pillows?",
    "Patient: Yes, I use extra pillows to breathe easier.",
    "Doctor: Noticed any swelling in your legs or ankles?",
    "Patient: No, no swelling.",
    "Doctor: Any night coughs or chest pain?",
    "Patient: Neither cough nor chest pain.",
    "Doctor: Feeling more tired than usual or any sudden mental changes?",
    "Patient: A bit forgetful but not more tired.",
    "Doctor: Can you share your recent vital signs?",
    "Patient: Temperature 98.0°F, heart rate 72 bpm, respiratory rate 18, oxygen saturation 92%, blood pressure 186/106.",
    "Doctor: Are you on any medications?",
    "Patient: Yes, Lisinopril, Furosemide, and Metoprolol.",
    "Doctor: How overall are you feeling since discharge?",
    "Patient: Okay, just taking it easy.",
    "Doctor: Any other concerns?",
    "Patient: No, thank you for your care.",
    f"Doctor: Goodbye, {fake_patient_name}, and keep monitoring your condition.",
]


@pytest.mark.timeout(5)
def test_summarizer_app():
    summary = summarizer_engine.summarize(test_transcript)

    print(summary)

    assert len(summary.patient_overview) > 10
    assert len(summary.current_symptoms) >= 1
    assert summary.vital_signs
    assert len(summary.current_medications) >= 1
