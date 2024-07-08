import dataclasses
import json

from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_openai import ChatOpenAI

from reco_analysis.summarizer_app.prompts import system_message_summarize_json

default_model = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo")


@dataclasses.dataclass
class VitalSigns:
    temperature: float | None
    heart_rate: float | None
    respiratory_rate: float | None
    oxygen_saturation: float | None
    blood_pressure_systolic: float | None
    blood_pressure_diastolic: float | None
    weight: float | None


@dataclasses.dataclass
class TranscriptSummary:
    patient_overview: str
    current_symptoms: list[str]
    vital_signs: VitalSigns
    current_medications: list[str]
    summary: list[str]


def summarize(
    patient_transcript,
    model: ChatOpenAI = default_model,
    system_prompt: str = system_message_summarize_json,
) -> TranscriptSummary:
    """Summarizes a patient transcript.

    Args:
        patient_transcript (str): The patient transcript to summarize.
        model (ChatOpenAI, optional): The model to use for summarization.
            Defaults to default_model.
        system_prompt (str, optional): The system prompt to use.
    """

    parser = StrOutputParser()
    prompt_template = ChatPromptTemplate.from_messages([("system", system_prompt)])

    chain = prompt_template | model | parser
    result = chain.invoke({"text": patient_transcript})

    try:
        # Process the result, remove markdown and convert to JSON
        processed_result = json.loads(
            result.replace("```json", "").replace("```", "").replace("\n", "")
        )
        return TranscriptSummary(
            patient_overview=processed_result["patient_overview"],
            current_symptoms=processed_result["current_symptoms"],
            vital_signs=VitalSigns(
                temperature=processed_result["vital_signs"]["temperature"],
                heart_rate=processed_result["vital_signs"]["heart_rate"],
                respiratory_rate=processed_result["vital_signs"]["respiratory_rate"],
                oxygen_saturation=processed_result["vital_signs"]["oxygen_saturation"],
                blood_pressure_systolic=processed_result["vital_signs"]["blood_pressure_systolic"],
                blood_pressure_diastolic=processed_result["vital_signs"][
                    "blood_pressure_diastolic"
                ],
                weight=processed_result["vital_signs"]["weight"],
            ),
            current_medications=processed_result["current_medications"],
            summary=processed_result["summary"],
        )

    except json.JSONDecodeError as e:
        raise ValueError("Failed to decode JSON from model output") from e


# Uncomment out all code below to test locally
# ------------------------------------------------

# import os
# import random

# import dotenv

# env_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
# dotenv.load_dotenv(env_file_path)

# # Specify the path to an example JSON file
# transcripts_version = "1.0"
# current_file_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.join(__file__))))
# json_file_path = (
#     f"{current_file_path}/data/patients/patients_{transcripts_version}_with_transcripts.json"
# )
# print(json_file_path)
# with open(json_file_path, "r") as json_file:
#     patients = json.load(json_file)
# random_key = random.choice(list(patients.keys()))
# patient_transcript = "".join(patients[random_key]["chat_transcript"])
# print(patient_transcript)


# # Uncomment the line below to test locally (this line should not be deployed to AWS Lambda)
# print(summarize(patient_transcript))
