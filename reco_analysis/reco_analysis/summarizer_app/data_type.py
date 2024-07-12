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

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclasses.dataclass
class TranscriptSummary:
    patient_overview: str
    current_symptoms: str
    vital_signs: VitalSigns
    current_medications: str
    summary: str

    @staticmethod
    def from_dict(data: dict) -> "TranscriptSummary":
        return TranscriptSummary(
            patient_overview=data["patient_overview"],
            current_symptoms=data["current_symptoms"],
            vital_signs=VitalSigns(
                temperature=data["vital_signs"]["temperature"],
                heart_rate=data["vital_signs"]["heart_rate"],
                respiratory_rate=data["vital_signs"]["respiratory_rate"],
                oxygen_saturation=data["vital_signs"]["oxygen_saturation"],
                blood_pressure_systolic=data["vital_signs"]["blood_pressure_systolic"],
                blood_pressure_diastolic=data["vital_signs"]["blood_pressure_diastolic"],
                weight=data["vital_signs"]["weight"],
            ),
            current_medications=data["current_medications"],
            summary=data["summary"],
        )

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
