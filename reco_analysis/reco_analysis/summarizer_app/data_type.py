import dataclasses
import json


@dataclasses.dataclass
class VitalSigns:
    temperature: float | None
    heart_rate: float | None
    respiratory_rate: float | None
    oxygen_saturation: float | None
    blood_pressure_systolic: float | None
    blood_pressure_diastolic: float | None
    weight: float | None

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self))


@dataclasses.dataclass
class TranscriptSummary:
    patient_overview: str
    current_symptoms: str
    vital_signs: VitalSigns
    current_medications: str
    summary: str

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self))
