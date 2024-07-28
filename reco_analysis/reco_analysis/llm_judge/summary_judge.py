import dataclasses
import hashlib
import json
from collections import defaultdict

import pandas as pd
from dotenv import load_dotenv
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv()

presence_description = "Does the SUMMARY json output contain a section with the key '{topic}'? Note that this criteria looks for the presence of a section, and not whether the section agrees or matches with TRANSCRIPT."

judge_criteria = {
    # summary content
    "intro_patient_present": presence_description.format(topic="patient_overview")
    + " Also, does the SUMMARY introduce patient by name?",
    "current_symptoms_present": presence_description.format(topic="current_symptoms"),
    "vital_signs_present": presence_description.format(topic="vital_signs"),
    "medications_present": presence_description.format(topic="current_medications"),
    "summary_overview_present": presence_description.format(topic="summary")
    + " Also, does this section give an overview of the content of the TRANSCRIPT",
    # accuracy of summary
    "symptoms_agree": "Does 'current_symptoms' section in the SUMMARY loosely agree with TRANSCRIPT? Specifically, in SUMMARY, please look in the 'current_symptoms' section only and ignore the 'patient_overview' and 'summary' sections. If there's a symptom that the patient is actively experiencing in 'summary' or 'patient_overview', that symptom must be present in the 'current_symptoms' too. This includes synonym phrases (e.g. 'prop up with pillows' equals to 'orthopnea'). Please look for a loose match only, and ignore the accuracy of mentioned symptoms, i.e. please ignore judging on descriptions of symptom's frequency/severity/details (e.g. 'on and off', 'severe', 'only when moving'). E.g., if TRANSCRIPT says 'chest pain on and off' and SUMMARY says 'chest pain' only, the criteria is still met (output as 1).",
    "vital_signs_agree": "Do the vital signs in the SUMMARY and TRANSCRIPT agree?",
    "meds_agree": "Do the medications in the SUMMARY and TRANSCRIPT agree?",
    # quality of summary
    "no_diagnose": "The SUMMARY is free from interpretation of results (avoided words like 'stable') and is free from diagnosis. Note that narration of patient's words is allowed (like 'patient thinks that they have...' or 'patient is experiencing...' or 'patient confirms that...'); still output a result of 1. Notes of advice like reminder to take meds or monitor symptoms are also allowed. However, predictions of future events (patient is likely/unlikely to...) are interpretations and are not allowed (mark as 0).",
}

system_message_summary_judge = (
    """You are evaluating a summarization engine that has generated a SUMMARY of a doctor-patient dialogue TRANSCRIPT based on a set of criteria. Your evaluation will consist of answering specific questions about the SUMMARY with 1 (Yes) and 0 (No) responses. The SUMMARY quality will depend on the TRANSCRIPT.
{output_format}

CRITERIA (CSV column names, then a description):
"""
    + "\n".join([f"{k}, {v}" for k, v in judge_criteria.items()])
    + """

ADDITIONAL INFORMATION: the following are common heart failure symptoms and their descriptions. Any mention of these medical terms or similar phrases do not count as a "diagnosis" in the context of this evaluation. If the patient claims some of these phrases for themselves (e.g. "I need to prop myself up with pillows"), it is a symptom and not a diagnosis, and the symptom should have been included in the symptoms list (e.g. "orthopnea" or "needs pillows" should be present).
- Dyspnea: shortness of breath, whether occurring at rest, walking, or climbing stairs
- Paroxysmal Nocturnal Dyspnea (PND): sudden shortness of breath that wakes patient up at night
- Orthopnea: needing to prop up with pillows to breathe comfortably while lying down
- Edema: swelling in your ankles or legs
- Nocturnal Cough: a cough especially at night
- Chest Pain
- Fatigue and Mental Status: feeling more tired than usual ("feeling tired" and "fatigue" are synonyms), or experience sudden changes in mental clarity (or mental status)

ADDITIONAL INFORMATION: "Do you need to prop yourself up with pillows to breathe comfortably" is a direct question on orthopnea (which is a term that patients don't understand), and as such, "Orthopnea" and "needing to prop up with pillows" are considered as one and the same.
- Orthopnea is often omitted in 'current_symptoms' by the summarizer when a patient claims they need pillows to prop up while laying flat; when this happens, it is a criteria violation for `current_symptoms_agree`.
- However, if the 'current_symptoms' section mentions 'orthopnea' but the TRANSCRIPT says only needing pillows (no explicit mention of 'orthopnea'), it is not a criteria violation (keep the score as 1).

"""
)

output_csv_format = """Generate a CSV row with the appropriate 1 or 0 for each criteria in the order specified below."""

output_reasoning_format = """In separate lines, state each criteria's value (1 or 0) and briefly explain your reasoning if it's a 0. When explaining reasoning, be very specific and please refer to texts in SUMMARY that is the offender. If it's a 1 (yes), leave the reasoning empty.
Lastly, in one last new line, please provide any short additional observations or suggestions for improvement (1 sentence), but do not repeat evaluation points previously made.
For example:
intro_patient,1,""
current_symptoms,0,"No symptoms are reported in SUMMARY"
vital_signs_agree,0,"Heart rate in SUMMARY is 130, but in TRANSCRIPT it's 131"
meds_agree,0,"Vitamins reported in SUMMARY is not in TRANSCRIPT"
write your one-sentence observation/improvement here
"""

human_message_summary_judge = """
TRANSCRIPT: {transcript}

SUMMARY: {summary}
"""

improvement_prompt_text = """You are tasked with improving a summarization engine's prompt, which generates summaries of doctor-patient dialogues. You will be given a list of learnings generated from an automated evaluation of the engine's summaries. Your task is to provide a revised prompt that addresses the learnings. Return your revised prompt as a string.

ORIGINAL PROMPT:
```
{original_summarization_engine_prompt}
```
"""

improvement_additional_instructions = """Additionally, apply JSON best practices to keep the outputs processable by downstream systems. After generating the new prompt, please summarize the key changes you made to the prompt under a "KEY CHANGES" section in the response."""


@dataclasses.dataclass
class ScoreReasoning:
    value: int
    reasoning: str


@dataclasses.dataclass
class SummaryJudgeEvaluation:
    intro_patient: ScoreReasoning
    current_symptoms: ScoreReasoning
    vital_signs: ScoreReasoning
    medications: ScoreReasoning
    summary_overview: ScoreReasoning
    symptoms_agree: ScoreReasoning
    vital_signs_agree: ScoreReasoning
    meds_agree: ScoreReasoning
    no_diagnose: ScoreReasoning
    observations: str

    def to_dict(self):
        return {
            "intro_patient": self.intro_patient.value,
            "intro_patient_reasoning": self.intro_patient.reasoning,
            "current_symptoms": self.current_symptoms.value,
            "current_symptoms_reasoning": self.current_symptoms.reasoning,
            "vital_signs": self.vital_signs.value,
            "vital_signs_reasoning": self.vital_signs.reasoning,
            "medications": self.medications.value,
            "medications_reasoning": self.medications.reasoning,
            "summary_overview": self.summary_overview.value,
            "summary_overview_reasoning": self.summary_overview.reasoning,
            "symptoms_agree": self.symptoms_agree.value,
            "symptoms_agree_reasoning": self.symptoms_agree.reasoning,
            "vital_signs_agree": self.vital_signs_agree.value,
            "vital_signs_agree_reasoning": self.vital_signs_agree.reasoning,
            "meds_agree": self.meds_agree.value,
            "meds_agree_reasoning": self.meds_agree.reasoning,
            "no_diagnose": self.no_diagnose.value,
            "no_diagnose_reasoning": self.no_diagnose.reasoning,
            "observations": self.observations,
        }


class SummaryJudge:
    def __init__(self, model_name="gpt-4o-mini"):
        self.model = ChatOpenAI(temperature=0.0, model_name=model_name)
        self.cache: dict[tuple[str, str], SummaryJudgeEvaluation] = defaultdict(dict)

    def _generate_hash(self, transcript, summary):
        """Generate a hash from the transcript and summary for caching."""
        hash_obj = hashlib.sha256()
        hash_obj.update(str(transcript).encode("utf-8"))
        hash_obj.update(str(summary).encode("utf-8"))
        return hash_obj.hexdigest()

    @staticmethod
    def parse_response(
        response_content: str, expected_fields=len(judge_criteria)
    ) -> SummaryJudgeEvaluation:
        response_list = response_content.split("\n")[0:expected_fields]
        if len(response_list) != expected_fields:
            return {"error": "Invalid response count"}
        response_dict = {}
        for response in response_list:
            if response:
                # split by first two commas, but keep the rest of the string
                response_split = response.split(",", 2)
                response_dict[response_split[0]] = ScoreReasoning(
                    value=int(response_split[1]), reasoning=response_split[2].strip('"')
                )

        # remainder text is the observations
        response_dict["observations"] = "\n".join(
            response_content.split("\n")[expected_fields:]
        ).strip()

        return SummaryJudgeEvaluation(**response_dict)

    def evaluate_single(
        self, patient_id: str, transcript: str | list[str], summary: str | dict
    ) -> SummaryJudgeEvaluation:

        if isinstance(summary, dict):
            summary_str = json.dumps(summary)
        else:
            summary_str = summary

        hash_key = self._generate_hash(str(transcript), summary_str)
        cache_key = (str(patient_id), hash_key)

        if cache_key in self.cache:
            print("Using cached results.")
            return self.cache[cache_key]

        # Construct prompt for the LLM
        prompt = (
            SystemMessage(
                content=system_message_summary_judge.format(output_format=output_reasoning_format)
            )
            + human_message_summary_judge
        )
        response = self.model.invoke(
            prompt.format_messages(transcript=transcript, summary=summary)
        )

        # Parse and store results
        eval = self.parse_response(response.content)
        self.cache[cache_key] = eval

        return eval

    def evaluate_batch(
        self, entries: list[tuple[str, str | list[str], str | dict]]
    ) -> pd.DataFrame:
        """Evaluate a batch of summaries.

        Args:
            entries (list): List of tuples containing (patient_id, transcript, summary)."""
        results: list[SummaryJudgeEvaluation] = []
        for patient_id, transcript, summary in entries:
            result = {"transcript_number": patient_id}
            result.update(self.evaluate_single(patient_id, transcript, summary).to_dict())
            results.append(result)

        return pd.DataFrame(results)

    def suggest_improvement(
        self,
        original_prompt: str,
        additional_instructions: str = improvement_additional_instructions,
    ) -> str:
        """Generate suggestions for improving the original summarization prompt."""
        prompt = SystemMessage(
            content=improvement_prompt_text.format(
                original_summarization_engine_prompt=original_prompt
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

    from reco_analysis.summarizer_app import prompts

    judge = SummaryJudge(model_name="gpt-3.5-turbo")  # cheaper model for testing

    # import data from hidden S3 folder
    module_path = os.path.dirname(os.path.abspath(__file__))
    transcripts_version = "1.0"
    transcripts_json_file_path = (
        module_path
        + "/../data/patients/patients_1.0_with_transcripts_terminated_manual_correct.json"
    )
    with open(transcripts_json_file_path, "r") as json_file:
        transcripts = json.load(json_file)

    summaries_json_file_path = module_path + "/../data/patients/patients_1.0_summaries.json"
    with open(summaries_json_file_path, "r") as json_file:
        summaries = json.load(json_file)

    # Additionally make tweaks to JSON keys for this evaluation
    keys_to_convert = {
        "Patient Overview": "patient_overview",
        "Current Symptoms": "current_symptoms",
        "Vital Signs": "vital_signs",
        "Current Medications": "current_medications",
        "Summary": "summary",
    }
    for patient_id, summary in summaries.items():
        new_summary = {}
        for key, value in summary["summary"].items():
            if key in keys_to_convert:
                new_summary[keys_to_convert[key]] = value
            else:
                new_summary[key] = value
        summaries[patient_id]["summary"] = new_summary

    patient_id = list(summaries.keys())[0]
    transcript = transcripts[patient_id]["chat_transcript"]
    summary = summaries[patient_id]["summary"]

    # Evaluate a single entry
    result = judge.evaluate_single(patient_id, transcript, summary)
    print(result)
    breakpoint()

    # Batch evaluation
    entries = [(patient_id, transcript, summary) for _ in range(2)]  # should be cached already
    batch_results = judge.evaluate_batch(entries)
    print(batch_results)
    breakpoint()

    # Suggest improvements
    original_prompt = prompts.system_message_summarize_json
    improvements = judge.suggest_improvement(original_prompt)
    print(improvements)
    breakpoint()
