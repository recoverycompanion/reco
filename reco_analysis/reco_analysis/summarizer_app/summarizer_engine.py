"""Summarizer Engine.

This module contains the summarizer engine, which is responsible for summarizing
patient transcripts. Input is a patient transcript, and output is a summary json
of the patient's overview, current symptoms, vital signs, current medications,
and a summary of the patient's condition."""

import json
import typing

from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from reco_analysis.summarizer_app import data_type
from reco_analysis.summarizer_app.prompts import system_message_summarize_json

default_model = ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo")


def summarize(
    patient_transcript: list[str],
    model: ChatOpenAI = default_model,
    system_prompt: str = system_message_summarize_json,
) -> typing.Tuple[data_type.TranscriptSummary, BaseMessage]:
    """Summarizes a patient transcript.

    Args:
        patient_transcript (list[str]): The patient transcript to summarize.
        model (ChatOpenAI, optional): The model to use for summarization.
            Defaults to default_model.
        system_prompt (str, optional): The system prompt to use.
    """
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "\n".join(patient_transcript)),
        ]
    )

    response = model.invoke(prompt_template.format_messages())
    result_summary = response.content

    try:
        # Process the result, remove markdown and convert to JSON
        processed_result = json.loads(
            result_summary.replace("```json", "").replace("```", "").replace("\n", "")
        )
        vitals: typing.Dict[str, typing.Any] = processed_result["vital_signs"]

        def get_vital(vital_name: str) -> typing.Any:
            ret = vitals.get(vital_name, None)
            if not isinstance(ret, (int, float)):
                return None
            return ret

        return (
            data_type.TranscriptSummary(
                patient_overview=processed_result["patient_overview"],
                current_symptoms=processed_result["current_symptoms"],
                vital_signs=data_type.VitalSigns(
                    temperature=get_vital("temperature"),
                    heart_rate=get_vital("heart_rate"),
                    respiratory_rate=get_vital("respiratory_rate"),
                    oxygen_saturation=get_vital("oxygen_saturation"),
                    blood_pressure_systolic=get_vital("blood_pressure_systolic"),
                    blood_pressure_diastolic=get_vital("blood_pressure_diastolic"),
                    weight=get_vital("weight"),
                ),
                current_medications=processed_result["current_medications"],
                summary=processed_result["summary"],
            ),
            response,
        )

    except json.JSONDecodeError as e:
        raise ValueError("Failed to decode JSON from model output") from e
