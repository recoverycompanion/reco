"""This module contains the TranscriptJudge class, which is used to evaluate the
quality of a conversation transcript generated by a doctor chatbot and a patient
LLM bot."""

import dataclasses
import hashlib
import json
from collections import defaultdict

import pandas as pd
from dotenv import load_dotenv
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv()

# Define the system message for the evaluation

symptom_ask_description = "Did the DOCTOR ask about '{symptom}' and was successful in getting a confirmation from PATIENT on whether the PATIENT experiences it?"

judge_criteria = {
    # introduction
    "patient_name": "Was the PATIENT's name mentioned by the DOCTOR?",
    # symptoms
    "dyspnea": symptom_ask_description.format(
        symptom="dyspnea (shortness of breath) at rest, while walking or climbing stairs"
    ),
    "pnd": symptom_ask_description.format(
        symptom="paroxysmal nocturnal dyspnea (PND) (sudden shortness of breath at night)"
    ),
    "orthopnea": symptom_ask_description.format(
        symptom="orthopnea (shortness of breath while lying flat)"
    ),
    "ankle_edema": symptom_ask_description.format(
        symptom="ankle edema or general lower extremity swelling (swelling in ankles or legs)"
    ),
    "nocturnal_cough": symptom_ask_description.format(
        symptom="nocturnal cough (coughing at night)"
    ),
    "chest_pain": symptom_ask_description.format(symptom="chest pain"),
    "fatigue": symptom_ask_description.format(symptom="fatigue"),
    "worsening_mental_status": symptom_ask_description.format(
        symptom="worsening mental status that is acute (sudden confusion or mental changes)"
    ),
    # medications
    "doctor_ask_medications": "Did the DOCTOR ask the PATIENT what medications they are on?",
    # vitals
    "temperature": "Did the DOCTOR ask for the PATIENT's temperature/body temperature?",
    "heart_rate": "Did the DOCTOR ask for the PATIENT's heart rate (pulse)?",
    "respiratory_rate": "Did the DOCTOR ask for the PATIENT's respiratory rate (number of breaths per minute)?",
    "oxygen_saturation": "Did the DOCTOR ask for the PATIENT's oxygen saturation (oxygen level in the blood)?",
    "blood_pressure": "Did the DOCTOR ask for the PATIENT's blood pressure (systolic and diastolic / upper and lower blood pressure numbers)?",
    "weight": "Did the DOCTOR ask for the PATIENT's weight (body weight)?",
    # hcp_quality
    "sympathetic_patient": "Was the DOCTOR sympathetic when the PATIENT reported symptoms or pain?",
    "reminder": "Did the DOCTOR remind the PATIENT to contact their healthcare provider if they notice any significant changes or worsening of symptoms?",
    "end_conversation": "Did the DOCTOR express care and encourage the PATIENT to reach out if they need further assistance at the end of the conversation?",
    "natural_conversation": "Did the conversation flow naturally without repetition?",
    "no_premature_end": "The conversation ended properly without a premature end.",
    # patient_quality
    "plain_language": "Did the PATIENT use plain language?",
    "consistent_symptoms": "Was the PATIENT consistent about their symptoms?",
    "no_confabulations": "Did the PATIENT avoid inventing information that contradicts the prompt (confabulations)?",
    "allow_doctor_questions": "Did the PATIENT allow the DOCTOR to ask questions and not take over the direction of the conversation (offering information before it’s asked for)?",
}

system_message_transcript_judge = """You are evaluating a dialogue TRANSCRIPT generated by a DOCTOR chatbot and a PATIENT LLM bot, based on a set of criteria.
Your evaluation will consist of answering specific questions about the DOCTOR/PATIENT bot with 1 (Yes) and 0 (No) responses.
The DOCTOR bot quality should not depend on the PATIENT.
The PATIENT bot quality however does depend on its own prompt (PATIENT_PROMPT).
{output_format}

CRITERIA (column name, then a description):
""" + "\n".join(
    [f"'{k}': {v}" for k, v in judge_criteria.items()]
)

output_csv_format = """Generate a CSV row with the appropriate 1 or 0 for each criteria in the order specified below."""

output_reasoning_format = """FORMAT: In separate lines, do the following:
1. first, state the criteria you're evaluating
2. second, make a brief assessment of the criteria on the TRANSCRIPT to justify your decision. After explaining your assessment/reasoning, end the line with 'criteria passed hence the score is 1' or 'criteria failed hence the score is 0'.
3. third, state each criteria's value (1 or 0).
Additionally, if there are issues that result in a 0, be very specific in your assessment portion and please refer to texts in the TRANSCRIPT that is the offender. If it's a 1 (yes), keep your assessment very short.
Lastly, after all criterias are evaluated, in one last new line, please provide any short additional observations or suggestions for improvement (2 sentences), but do not repeat evaluation points previously made.
For example:

patient_name,"The DOCTOR greeted the PATIENT by name; criteria passed hence the score is 1",1
dyspnea,"The DOCTOR was successful in getting a confirmation from the PATIENT that they don't have dyspnea or shortness of breath; criteria passed hence the score is 1",1
pnd,"The DOCTOR did not ask about PND in the conversation; criteria failed hence the score is 0",0
sympathetic_patient,"The DOCTOR ignored PATIENT after PATIENT writes 'I am feeling light-headed'; criteria failed hence the score is 0",0
consistent_symptoms,"The PATIENT says 'I have chest pain' but later says 'I have no chest pain'; criteria failed hence the score is 0",0
OBSERVATION:write your two-sentence observation/improvement here
"""

human_message_transcript_judge = """
PATIENT_PROMPT: {patient_prompt}

TRANSCRIPT: {transcript}
"""

improvement_prompt_text = """You are tasked with improving a doctor conversational chatbot prompt, which has been interacting with (synthetic) heart failure patients. You will be given the original prompts (which exists in two parts: SYSTEM_MESSAGE_DOCTOR and AI_GUIDANCE_DOCTOR) and a list of learnings generated from an automated evaluation of the chatbot's transcripts. Your task is to provide a revised prompt that addresses the learnings. Return your revised prompt as a string.

SYSTEM_MESSAGE_DOCTOR: ```{original_chatbot_system_message_doctor}```
AI_GUIDANCE_DOCTOR: ```{original_chatbot_ai_guidance_doctor}```
"""

improvement_additional_instructions = (
    """Focus on improving the quality of the conversation and the patient experience."""
    """After generating the new prompt, please summarize the key changes you made to the prompt under a "KEY CHANGES" section in the response."""
)


@dataclasses.dataclass
class ScoreReasoning:
    value: int | None
    reasoning: str | None


@dataclasses.dataclass
class TranscriptJudgeEvaluation:
    patient_name: ScoreReasoning
    dyspnea: ScoreReasoning
    pnd: ScoreReasoning
    orthopnea: ScoreReasoning
    ankle_edema: ScoreReasoning
    nocturnal_cough: ScoreReasoning
    chest_pain: ScoreReasoning
    fatigue: ScoreReasoning
    worsening_mental_status: ScoreReasoning
    doctor_ask_medications: ScoreReasoning
    temperature: ScoreReasoning
    heart_rate: ScoreReasoning
    respiratory_rate: ScoreReasoning
    oxygen_saturation: ScoreReasoning
    blood_pressure: ScoreReasoning
    weight: ScoreReasoning
    sympathetic_patient: ScoreReasoning
    reminder: ScoreReasoning
    end_conversation: ScoreReasoning
    natural_conversation: ScoreReasoning
    no_premature_end: ScoreReasoning
    plain_language: ScoreReasoning
    consistent_symptoms: ScoreReasoning
    no_confabulations: ScoreReasoning
    allow_doctor_questions: ScoreReasoning
    observations: str

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(score={self.overall_score()}, observations={self.observations})"

    def score_reasonings(self) -> dict[str, ScoreReasoning]:
        return {
            k: getattr(self, k)
            for k in self.__dataclass_fields__.keys()
            if isinstance(getattr(self, k), ScoreReasoning)
        }

    def to_dict(self):
        return {
            "patient_name": self.patient_name.value,
            "patient_name_reasoning": self.patient_name.reasoning,
            "dyspnea": self.dyspnea.value,
            "dyspnea_reasoning": self.dyspnea.reasoning,
            "pnd": self.pnd.value,
            "pnd_reasoning": self.pnd.reasoning,
            "orthopnea": self.orthopnea.value,
            "orthopnea_reasoning": self.orthopnea.reasoning,
            "ankle_edema_reasoning": self.ankle_edema.reasoning,
            "nocturnal_cough": self.nocturnal_cough.value,
            "nocturnal_cough_reasoning": self.nocturnal_cough.reasoning,
            "chest_pain": self.chest_pain.value,
            "chest_pain_reasoning": self.chest_pain.reasoning,
            "fatigue": self.fatigue.value,
            "fatigue_reasoning": self.fatigue.reasoning,
            "worsening_mental_status": self.worsening_mental_status.value,
            "worsening_mental_status_reasoning": self.worsening_mental_status.reasoning,
            "doctor_ask_medications": self.doctor_ask_medications.value,
            "doctor_ask_medications_reasoning": self.doctor_ask_medications.reasoning,
            "temperature": self.temperature.value,
            "temperature_reasoning": self.temperature.reasoning,
            "heart_rate": self.heart_rate.value,
            "heart_rate_reasoning": self.heart_rate.reasoning,
            "respiratory_rate": self.respiratory_rate.value,
            "respiratory_rate_reasoning": self.respiratory_rate.reasoning,
            "oxygen_saturation": self.oxygen_saturation.value,
            "oxygen_saturation_reasoning": self.oxygen_saturation.reasoning,
            "blood_pressure": self.blood_pressure.value,
            "blood_pressure_reasoning": self.blood_pressure.reasoning,
            "weight": self.weight.value,
            "weight_reasoning": self.weight.reasoning,
            "sympathetic_patient": self.sympathetic_patient.value,
            "sympathetic_patient_reasoning": self.sympathetic_patient.reasoning,
            "reminder": self.reminder.value,
            "reminder_reasoning": self.reminder.reasoning,
            "end_conversation": self.end_conversation.value,
            "end_conversation_reasoning": self.end_conversation.reasoning,
            "natural_conversation": self.natural_conversation.value,
            "natural_conversation_reasoning": self.natural_conversation.reasoning,
            "no_premature_end": self.no_premature_end.value,
            "no_premature_end_reasoning": self.no_premature_end.reasoning,
            "plain_language": self.plain_language.value,
            "plain_language_reasoning": self.plain_language.reasoning,
            "consistent_symptoms": self.consistent_symptoms.value,
            "consistent_symptoms_reasoning": self.consistent_symptoms.reasoning,
            "no_confabulations": self.no_confabulations.value,
            "no_confabulations_reasoning": self.no_confabulations.reasoning,
            "allow_doctor_questions": self.allow_doctor_questions.value,
            "allow_doctor_questions_reasoning": self.allow_doctor_questions.reasoning,
            "observations": self.observations,
        }

    def passed_criteria(self) -> dict[str, ScoreReasoning]:
        return {k: v for k, v in self.score_reasonings().items() if v.value == 1}

    def failed_criteria(self) -> dict[str, ScoreReasoning]:
        return {k: v for k, v in self.score_reasonings().items() if v.value == 0}

    def overall_score(self) -> float:
        all_scores = self.score_reasonings()
        sum_scores = sum([v.value if v.value is not None else 0 for v in all_scores.values()])
        return sum_scores / len(all_scores)


class TranscriptJudge:
    def __init__(self, model_name="gpt-4o-mini"):
        self.model = ChatOpenAI(temperature=0.0, model_name=model_name)
        self.cache: dict[tuple[str, str], TranscriptJudgeEvaluation] = defaultdict(dict)

    def _generate_hash(self, transcript: str | list[str], patient_prompt: str) -> str:
        hash_obj = hashlib.sha256()
        hash_obj.update(str(transcript).encode("utf-8"))
        hash_obj.update(str(patient_prompt).encode("utf-8"))
        return hash_obj.hexdigest()

    @staticmethod
    def parse_response(response_content: str):
        """
        Function to validate and parse the response.

        Example response
        'intro_patient,1,""\n'
        'current_symptoms,1,""\n'
        'symptoms_agree,0,"Nose bleeding was mentioned in the summary, but not in the transcript."\n'

        Args:
            response_content (str): Response content from the LLM

        Returns:
            TranscriptJudgeEvaluation: A dataclass object with the parsed response
        """
        response_list = response_content.split("\n")
        response_dict: dict[str, ScoreReasoning | str] = {}
        for response in response_list:
            if response:
                try:
                    (criteria, back_split) = response.split(",", 1)
                    (reasoning, value) = back_split.rsplit(",", 1)
                    response_dict[criteria] = ScoreReasoning(
                        value=int(value),
                        reasoning=reasoning.strip('"'),
                    )
                except ValueError:
                    # print(f"Error parsing response: {response}")
                    pass

        # additional wrangling on all:
        # find phrase 'criteria passed hence the score is 1' and 'criteria failed hence the score is 0'
        # if found, override the value with 1 or 0
        for key, value in response_dict.items():
            if "criteria passed hence the score is 1" in value.reasoning:
                response_dict[key].value = 1
            elif "criteria failed hence the score is 0" in value.reasoning:
                response_dict[key].value = 0

        # if there are any missing fields, fill them with None
        for field in judge_criteria.keys():
            if field not in response_dict:
                response_dict[field] = ScoreReasoning(value=None, reasoning=None)
                print(f"Missing field: {field}")

        # find a line that starts with 'observation:' and use it as the observation
        response_dict["observations"] = ""
        for line in response_content.split("\n"):
            if line.lower().startswith("observation:"):
                response_dict["observations"] = line.split(":", 1)[1].strip()
                break

        return TranscriptJudgeEvaluation(**response_dict)

    def evaluate_single(
        self, patient_id: str, transcript: str | list[str], patient_prompt: str
    ) -> TranscriptJudgeEvaluation:

        hash_key = self._generate_hash(transcript, patient_prompt)
        cache_key = (str(patient_id), hash_key)

        if cache_key in self.cache:
            print("Using cached results.")
            return self.cache[cache_key]

        # Construct prompt for the LLM
        prompt = (
            SystemMessage(
                content=system_message_transcript_judge.format(
                    output_format=output_reasoning_format
                )
            )
            + human_message_transcript_judge
        )
        response = self.model.invoke(
            prompt.format_messages(transcript=transcript, patient_prompt=patient_prompt)
        )

        # Parse and store results
        eval = self.parse_response(response.content)
        self.cache[cache_key] = eval

        return eval

    def evaluate_batch(self, entries: list[tuple[str, str | list[str], str]]) -> pd.DataFrame:
        """Evaluate a batch of transcripts.

        Args:
            entries (list): List of tuples containing (patient_id, transcript, patient_prompt)."""
        results: list[TranscriptJudgeEvaluation] = []
        for patient_id, transcript, patient_prompt in entries:
            try:
                result = {"transcript_number": patient_id}
                result.update(
                    self.evaluate_single(patient_id, transcript, patient_prompt).to_dict()
                )
                results.append(result)
            except Exception as e:
                print(f"Error evaluating transcript for patient {patient_id}: {e}")
                continue

        return pd.DataFrame(results)

    def suggest_improvement(
        self,
        original_chatbot_system_message_doctor: str,
        original_chatbot_ai_guidance_doctor: str,
        additional_instructions: str = improvement_additional_instructions,
    ) -> str:
        """Generate suggestions for improving the original doctor chatbot prompt."""
        prompt = SystemMessage(
            content=improvement_prompt_text.format(
                original_chatbot_system_message_doctor=original_chatbot_system_message_doctor,
                original_chatbot_ai_guidance_doctor=original_chatbot_ai_guidance_doctor,
            )
        )

        # feed in `observation` from all cached evaluations
        learnings_message = HumanMessage(
            content="LEARNINGS:\n" + "\n".join([eval.observations for eval in self.cache.values()])
        )

        overall_prompt = prompt + learnings_message

        if additional_instructions:
            overall_prompt += HumanMessage(content=additional_instructions)

        response = self.model.invoke(overall_prompt.format_messages())
        return response.content


# Example usage
if __name__ == "__main__":
    import os

    from reco_analysis.chatbot import prompts

    judge = TranscriptJudge()  # cheaper model for testing

    # import data from hidden S3 folder
    module_path = os.path.dirname(os.path.abspath(__file__))
    transcripts_version = "1.0"
    transcripts_json_file_path = (
        module_path + "/../../data/patients/patients_1.0_with_transcripts.json"
    )
    with open(transcripts_json_file_path, "r") as json_file:
        transcripts = json.load(json_file)

    patient_id = list(transcripts.keys())[0]
    transcript = transcripts[patient_id]["chat_transcript"]
    patient_prompt = transcripts[patient_id]["prompt"]

    # Evaluate a single entry
    result = judge.evaluate_single(patient_id, transcript, patient_prompt)
    print(result)
    breakpoint()

    # Batch evaluation
    entries = [
        (patient_id, transcript, patient_prompt) for _ in range(2)
    ]  # should be cached already
    batch_results = judge.evaluate_batch(entries)
    print(batch_results)
    breakpoint()

    # Suggest improvements
    improvements = judge.suggest_improvement(
        original_chatbot_system_message_doctor=prompts.system_message_doctor,
        original_chatbot_ai_guidance_doctor=prompts.ai_guidance_doctor,
    )
    print(improvements)
    breakpoint()
