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
    "patient_overview": {
        "intro_patient_present": presence_description.format(topic="patient_overview")
        + " Also, does the SUMMARY introduce patient by name?",
    },
    "current_symptoms": {
        "current_symptoms_present": presence_description.format(topic="current_symptoms"),
        "current_symptoms_agree": "Does 'current_symptoms' section in the SUMMARY loosely agree with TRANSCRIPT? If so, output as 1. Specifically, in SUMMARY, please look in the 'current_symptoms' section only and ignore the 'patient_overview' and 'summary' sections. If there's a symptom that the patient is actively experiencing in 'summary' or 'patient_overview', that symptom must be present in the 'current_symptoms' too. This includes synonym phrases (e.g. 'prop up with pillows' equals to 'orthopnea'). Please look for a loose match only, and ignore the accuracy of mentioned symptoms, i.e. please ignore judging on descriptions of symptom's frequency/severity/details (e.g. 'on and off', 'severe', 'only when moving'). E.g., if TRANSCRIPT says 'chest pain on and off' and SUMMARY says 'chest pain' only, the criteria is still met (output as 1). Note that symptoms not related to heart failure should be included.",
        # special case: orthopnea
        "orthopnea_agree": "Does the 'current_symptoms' section in the SUMMARY accurately represent the patient's claim of needing to prop up with pillows to breathe comfortably? If patient says they need pillows to prop up while laying flat, mark as 1 if 'orthopnea'/'pillows' is mentioned in 'current_symptoms', otherwise mark as 0. Alternatively, if the patient says they do not need pillows to prop up while laying flat, mark as 1 if 'orthopnea'/'pillows' is not mentioned in 'current_symptoms', otherwise mark as 0. Specifically, in SUMMARY, please look in the 'current_symptoms' section only and ignore the 'patient_overview' and 'summary' sections. In your assessment, first describe if patient needs pillows, then reiterate what's listed in 'current_symptoms' section (do not refer to other sections), then mention if 'orthopnea'/'pillows' is mentioned in 'current_symptoms' section, then make your comparison.",
    },
    "vital_signs": {
        "vital_signs_present": presence_description.format(topic="vital_signs"),
        "vital_signs_agree": "Do the vital signs in the SUMMARY and TRANSCRIPT agree?",
    },
    "current_medications": {
        "medications_present": presence_description.format(topic="current_medications"),
        "medications_agree": "Do the medications in the SUMMARY and TRANSCRIPT agree?",
    },
    "summary": {
        "summary_overview_present": presence_description.format(topic="summary")
        + " Also, does this section give an overview of the content of the TRANSCRIPT",
        "no_diagnose": "The SUMMARY is free from interpretation of results (avoided words like 'stable') and is free from diagnosis. Note that narration of patient's words is allowed (like 'patient thinks that they have...' or 'patient is experiencing...' or 'patient confirms that...'); still output a result of 1. Notes of advice like reminder to take meds or monitor symptoms are also allowed. However, predictions of future events (patient is likely/unlikely to...) are interpretations and are not allowed (mark as 0). These specific phrases are also not allowed: 'vital signs are stable', 'within normal range', 'heart rate is higher than normal', 'vital signs are within normal limits'.",
        # special cases: normality and stability
        "no_normality": "The SUMMARY does not contain any mention of 'normal' or 'within normal limits' in the context of patient's health. If the patient's health is described as 'normal' or 'within normal limits' in SUMMARY, mark as 0. Otherwise, mark as 1. In your assessment, please say if the idea of 'normal' is mentioned, then make your comparison.",
        "no_stability": "The SUMMARY does not contain any mention of 'stable' in the context of patient's health. If the patient's health is described as 'stable' in SUMMARY, mark as 0. Otherwise, mark as 1. In your assessment, please say if the idea of 'stable' is mentioned, then make your comparison.",
    },
}


system_message_summary_judge = """You are evaluating a summarization engine that has generated a SUMMARY of a doctor-patient dialogue TRANSCRIPT based on a set of criteria. Your evaluation will consist of answering specific questions about the SUMMARY with 1 (Yes) and 0 (No) responses. The SUMMARY quality will depend on the TRANSCRIPT.
{output_format}

CRITERIA (CSV column names, then a description):
{criteria}

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

output_csv_format = """Generate a CSV row with the appropriate 1 or 0 for each criteria in the order specified below."""

output_reasoning_format = """In separate lines, first make a brief assessment of the criteria on the SUMMARY to justify your decision, then state each criteria's value (1 or 0). When explaining your assessment/reasoning, if there are issues that result in a 0, be very specific and please refer to texts in SUMMARY that is the offender. If it's a 1 (yes/no issues), keep your assessment very short.
Lastly, in one last new line, please provide any short additional observations or suggestions for improvement (2 sentences), but do not repeat evaluation points previously made. Be specific with examples, and be concise with words.
For example:
intro_patient_present,"Patient name is introduced; criteria passed hence the score is 1",1
current_symptoms_present,"No symptoms are reported in SUMMARY; criteria failed hence the score is 0",0
orthopnea_agree,"Patient needs pillows to prop up while laying flat; current_symptoms listed: 'dyspnea, fatigue'; 'orthopnea' is not listed; criteria failed hence the score is 0",0
vital_signs_agree,"Heart rate in SUMMARY is 130, but in TRANSCRIPT it's 131; criteria failed hence the score is 0",0
current_symptoms_agree,"Current symptoms in SUMMARY match TRANSCRIPT; criteria passed hence the score is 1",1
medications_agree,"Vitamins reported in SUMMARY is not in TRANSCRIPT; criteria failed hence the score is 0",0
OBSERVATION:write your two-sentence observation/improvement here
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

improvement_additional_instructions = """Additionally, apply JSON best practices to keep the outputs processable by downstream systems.
Before generating the new prompt, summarize a "KEY GOALS" section for the prompt improvement for what you're about to do, pulling in specific examples from the learnings.
Then, write a "REVISED PROMPT" section making changes to ORIGINAL PROMPT. Be specific on what the new prompt should do by referring to the learnings.
After generating the new prompt, please summarize the key changes you made to the prompt under a "KEY CHANGES" section in the response."""


def get_system_message_summary_judge(judge_criteria: dict):
    """Generate a system message for the summary judge."""
    return system_message_summary_judge.format(
        output_format=output_reasoning_format,
        criteria="\n".join([f"`{key}`: {value}" for key, value in judge_criteria.items()]),
    )


def parse_response(response_content: str) -> dict:
    """Function to validate and parse the response.

    Example response:
        'intro_patient,"",1\n'
        'current_symptoms,"",1\n'
        'symptoms_agree,"Nose bleeding was mentioned in the summary, but not in the transcript.",0\n'

    Desired output
        {"intro_patient": {"value": 1, "reasoning": ""}, "current_symptoms": {"value": 1, "reasoning": ""}, ...}
    """
    response_list = response_content.split("\n")
    response_dict = {}
    for response in response_list:
        if response:
            try:
                (criteria, back_split) = response.split(",", 1)
                (reasoning, value) = back_split.rsplit(",", 1)
                response_dict[criteria] = {"value": int(value), "reasoning": reasoning.strip('"')}
            except ValueError:
                # print(f"Error parsing response: {response}")
                pass

    # additional wrangling on all: find phrase 'criteria passed hence the score is 1' and 'criteria failed hence the score is 0'
    # if found, override the value with 1 or 0
    for key, value in response_dict.items():
        if "criteria passed hence the score is 1" in value["reasoning"]:
            response_dict[key]["value"] = 1
        elif "criteria failed hence the score is 0" in value["reasoning"]:
            response_dict[key]["value"] = 0

    # find a line that starts with 'observation:' and use it as the observation
    response_dict["observations"] = ""
    for line in response_content.split("\n"):
        if line.lower().startswith("observation:"):
            response_dict["observations"] = line.split(":", 1)[1].strip()
            break

    return response_dict


def combine_current_symptoms_agree(result_dict: dict):
    """If orthopnea_agree is present, combine it with current_symptoms_agree."""
    if "orthopnea_agree" in result_dict and "current_symptoms_agree" in result_dict:
        modified_result_dict = result_dict.copy()
        modified_result_dict["current_symptoms_agree"]["value"] = (
            result_dict["current_symptoms_agree"]["value"]
            and result_dict["orthopnea_agree"]["value"]
        )
        modified_result_dict["current_symptoms_agree"]["reasoning"] = (
            result_dict["current_symptoms_agree"]["reasoning"]
            + "; "
            + result_dict["orthopnea_agree"]["reasoning"]
        )
        return modified_result_dict

    return result_dict


def combine_no_diagnose(result_dict: dict):
    """Combine no_normality and no_stability into no_diagnose."""
    if (
        "no_normality" in result_dict
        and "no_stability" in result_dict
        and "no_diagnose" in result_dict
    ):
        modified_result_dict = result_dict.copy()
        modified_result_dict["no_diagnose"]["value"] = (
            result_dict["no_diagnose"]["value"]
            and result_dict["no_normality"]["value"]
            and result_dict["no_stability"]["value"]
        )
        modified_result_dict["no_diagnose"]["reasoning"] = (
            result_dict["no_diagnose"]["reasoning"]
            + " "
            + result_dict["no_normality"]["reasoning"]
            + " "
            + result_dict["no_stability"]["reasoning"]
        )
        return modified_result_dict

    return result_dict


@dataclasses.dataclass
class ScoreReasoning:
    value: int
    reasoning: str


@dataclasses.dataclass
class SummaryJudgeEvaluation:
    intro_patient_present: ScoreReasoning
    current_symptoms_present: ScoreReasoning
    vital_signs_present: ScoreReasoning
    medications_present: ScoreReasoning
    summary_overview_present: ScoreReasoning

    current_symptoms_agree: ScoreReasoning
    orthopnea_agree: ScoreReasoning
    vital_signs_agree: ScoreReasoning
    medications_agree: ScoreReasoning

    no_diagnose: ScoreReasoning
    no_normality: ScoreReasoning
    no_stability: ScoreReasoning

    observations: str

    def to_dict(self):
        return {
            "intro_patient_present": self.intro_patient_present.value,
            "intro_patient_present_reasoning": self.intro_patient_present.reasoning,
            "current_symptoms_present": self.current_symptoms_present.value,
            "current_symptoms_present_reasoning": self.current_symptoms_present.reasoning,
            "vital_signs_present": self.vital_signs_present.value,
            "vital_signs_present_reasoning": self.vital_signs_present.reasoning,
            "medications_present": self.medications_present.value,
            "medications_present_reasoning": self.medications_present.reasoning,
            "summary_overview_present": self.summary_overview_present.value,
            "summary_overview_present_reasoning": self.summary_overview_present.reasoning,
            "current_symptoms_agree": self.current_symptoms_agree.value,
            "current_symptoms_agree_reasoning": self.current_symptoms_agree.reasoning,
            "orthopnea_agree": self.orthopnea_agree.value,
            "orthopnea_agree_reasoning": self.orthopnea_agree.reasoning,
            "vital_signs_agree": self.vital_signs_agree.value,
            "vital_signs_agree_reasoning": self.vital_signs_agree.reasoning,
            "medications_agree": self.medications_agree.value,
            "medications_agree_reasoning": self.medications_agree.reasoning,
            "no_diagnose": self.no_diagnose.value,
            "no_diagnose_reasoning": self.no_diagnose.reasoning,
            "no_normality": self.no_normality.value,
            "no_normality_reasoning": self.no_normality.reasoning,
            "no_stability": self.no_stability.value,
            "no_stability_reasoning": self.no_stability.reasoning,
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

    def evaluate_single(
        self, patient_id: str, transcript: str | list[str], summary: dict
    ) -> SummaryJudgeEvaluation:

        summary_str = json.dumps(summary)
        hash_key = self._generate_hash(str(transcript), summary_str)
        cache_key = (str(patient_id), hash_key)

        if cache_key in self.cache:
            print("Using cached results.")
            return self.cache[cache_key]

        results_dict = {}
        all_responses = {}
        all_observations = ""
        for section_name in summary.keys():
            print("evaluating", section_name)
            prompt = (
                SystemMessage(
                    content=get_system_message_summary_judge(judge_criteria[section_name])
                )
                + human_message_summary_judge
            )
            summary_subset = {section_name: summary[section_name]}

            # Get the response
            response = self.model.invoke(
                prompt.format_messages(transcript=transcript, summary=summary_subset)
            )
            all_responses[section_name] = response
            subset_results_dict = parse_response(response.content)

            # filter to only the criteria + observations
            subset_results_dict = {
                k: v
                for k, v in subset_results_dict.items()
                if k in judge_criteria[section_name].keys() or k == "observations"
            }

            # special cases of combining results
            if section_name == "current_symptoms":
                subset_results_dict = combine_current_symptoms_agree(subset_results_dict)
            elif section_name == "summary":
                subset_results_dict = combine_no_diagnose(subset_results_dict)

            if "observations" in subset_results_dict:
                observation = subset_results_dict.pop("observations")
                if observation:
                    all_observations += f"Observations for {section_name}:\n{observation}\n\n"

            # iterate through subset_response_dict; convert all to ScoreReasoning
            for key, value in subset_results_dict.items():
                subset_results_dict[key] = ScoreReasoning(
                    value=value["value"], reasoning=value["reasoning"]
                )

            results_dict.update(subset_results_dict)

        results_dict["observations"] = all_observations

        ret = SummaryJudgeEvaluation(**results_dict)
        self.cache[cache_key] = ret
        return ret

    def evaluate_batch(self, entries: list[tuple[str, str | list[str], dict]]) -> pd.DataFrame:
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
        + "/../../data/patients/patients_1.0_with_transcripts_terminated_manual_correct.json"
    )
    with open(transcripts_json_file_path, "r") as json_file:
        transcripts = json.load(json_file)

    summaries_json_file_path = module_path + "/../../data/patients/patients_1.0_summaries.json"
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

    patient_id = list(summaries.keys())[1]
    transcript = transcripts[patient_id]["chat_transcript"]
    summary = summaries[patient_id]["summary"]

    assert isinstance(summary, dict)

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
