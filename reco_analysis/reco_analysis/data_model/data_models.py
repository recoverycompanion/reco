import json
import os
import typing
import uuid

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Engine,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

from reco_analysis.summarizer_app import data_type as summarizer_data_type

env_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(env_file_path)

ENVIRONMENT = os.getenv("POSTGRES_DB_ENVIRONMENT") or "DEV"
if ENVIRONMENT not in ["DEV", "PROD"]:
    raise ValueError("POSTGRES_DB_ENVIRONMENT must be either 'DEV' or 'PROD'")


USER = os.getenv(f"POSTGRES_DB_{ENVIRONMENT}_USER")
PASSWORD = os.getenv(f"POSTGRES_DB_{ENVIRONMENT}_PASSWORD")
HOST = os.getenv(f"POSTGRES_DB_{ENVIRONMENT}_HOST")
PORT = os.getenv(f"POSTGRES_DB_{ENVIRONMENT}_PORT")
DB = os.getenv(f"POSTGRES_DB_{ENVIRONMENT}_NAME")


def connection_env_vars_available() -> bool:
    return all([USER, PASSWORD, HOST, PORT, DB])


DB_URL = (
    f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}" if connection_env_vars_available() else ""
)

ENGINE: Engine | None = None
SESSION: Session | None = None


def get_engine(db_url: str = DB_URL) -> "Engine":
    global ENGINE
    if ENGINE is None:
        ENGINE = create_engine(db_url)
    return ENGINE


def get_session() -> Session:
    global SESSION
    if SESSION is None:
        SESSION = sessionmaker(bind=get_engine())()
    return SESSION


Base = declarative_base()

default_hcp_email = "mike.khor@berkeley.edu"  # for now


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(60), nullable=False)
    healthcare_provider_id = Column(Integer, ForeignKey("healthcare_providers.id"), nullable=True)

    healthcare_provider = relationship("HealthcareProvider", back_populates="patients")
    conversation_sessions = relationship(
        "ConversationSession", back_populates="patient", uselist=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # after init, also set healthcare_provider_id to default_hcp, if not set
        if not self.healthcare_provider_id:
            try:
                hcp = HealthcareProvider.get_by_email(default_hcp_email, get_session())
                self.healthcare_provider_id = hcp.id
            except ValueError:
                pass

    def __repr__(self):
        return (
            f"Patient(username='{self.username}', first_name='{self.first_name}', "
            f"last_name='{self.last_name}', email='{self.email}', "
            f"created_at='{self.created_at}', updated_at='{self.updated_at}')"
        )

    def new_session(self, summary: str | None = None) -> "ConversationSession":
        return ConversationSession(patient_id=self.id, summary=summary)

    @staticmethod
    def get_by_id(patient_id: int, session: Session) -> "Patient":
        ret = session.query(Patient).filter(Patient.id == patient_id).first()
        if not ret:
            raise ValueError(f"Patient with id {patient_id} not found")
        return ret

    @staticmethod
    def get_by_username(username: str, session: Session) -> "Patient":
        ret = session.query(Patient).filter(Patient.username == username).first()
        if not ret:
            raise ValueError(f"Patient with username {username} not found")
        return ret

    @staticmethod
    def new_patient(
        username: str, first_name: str, last_name: str, email: str, password: str, session: Session
    ) -> "Patient":
        if session.query(Patient).filter(Patient.username == username).first():
            raise ValueError(f"Patient with username '{username}' already exists")

        if session.query(Patient).filter(Patient.email == email).first():
            raise ValueError(f"Patient with email '{email}' already exists")

        new_patient = Patient(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )
        session.add(new_patient)
        session.commit()
        return new_patient

    @staticmethod
    def get_all_patients(session: Session) -> list["Patient"]:
        return session.query(Patient).all()

    def get_latest_conversation_session(self) -> "ConversationSession | None":
        """Get the latest conversation session for the patient. If no session
        exists, returns None."""
        if not self.conversation_sessions:
            return None
        return self.conversation_sessions[-1]


class HealthcareProvider(Base):
    __tablename__ = "healthcare_providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    email = Column(String(120), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    patients = relationship("Patient", back_populates="healthcare_provider", uselist=True)

    def __repr__(self):
        return (
            f"HealthcareProvider("
            f"id='{self.id}', "
            f"first_name='{self.first_name}', "
            f"last_name='{self.last_name}', "
            f"email='{self.email}', "
            f"created_at='{self.created_at}', "
            f"updated_at='{self.updated_at}')"
        )

    @staticmethod
    def get_by_id(provider_id: int, session: Session) -> "HealthcareProvider":
        ret = (
            session.query(HealthcareProvider).filter(HealthcareProvider.id == provider_id).first()
        )
        if not ret:
            raise ValueError(f"Healthcare provider with id {provider_id} not found")
        return ret

    @staticmethod
    def get_by_email(email: str, session: Session) -> "HealthcareProvider":
        ret = session.query(HealthcareProvider).filter(HealthcareProvider.email == email).first()
        if not ret:
            raise ValueError(f"Healthcare provider with email {email} not found")
        return ret

    @staticmethod
    def create_default_healthcare_provider(session: Session) -> "HealthcareProvider":
        default_hcp = HealthcareProvider(
            first_name="Ray",
            last_name="ReCo",
            description="A friendly default healthcare provider",
            email=default_hcp_email,
        )
        session.add(default_hcp)
        session.commit()
        return default_hcp


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    summary = Column(
        Text, nullable=True
    )  # Summary of the session created by the summarization engine

    patient = relationship("Patient", back_populates="conversation_sessions", uselist=False)
    messages = relationship("Message", back_populates="session")
    completed = Column(Boolean, default=False)

    def __repr__(self):
        return (
            f"ConversationSession(patient_id='{self.patient_id}', created_at='{self.created_at}', "
            f"updated_at='{self.updated_at}', summary='{self.summary}')"
        )

    @staticmethod
    def get_by_id(session_id: uuid.UUID, session: Session) -> "ConversationSession":
        ret = (
            session.query(ConversationSession).filter(ConversationSession.id == session_id).first()
        )
        if not ret:
            raise ValueError(f"Session with id {session_id} not found")
        return ret

    @staticmethod
    def new_session(patient_id: int, session: Session) -> "ConversationSession":
        new_session = ConversationSession(patient_id=patient_id)
        session.add(new_session)
        session.commit()
        return new_session

    def mark_as_completed(self, session: Session) -> None:
        """Mark the session as completed once the conversation is done."""
        self.completed = True
        session.commit()

    def get_transcript(self) -> list[str]:
        ret = []
        for message in self.messages:
            message = typing.cast(Message, message)
            ret.append(message.as_transcript_line())
        return ret

    def save_summary(
        self,
        summary: summarizer_data_type.TranscriptSummary,
        response_message: BaseMessage,
        session: Session,
    ) -> None:
        """Save the summary and response message to the database."""
        to_save = {
            "summary": summary.to_dict(),
            "response_metadata": response_message.response_metadata,
        }
        self.summary = json.dumps(to_save)
        session.commit()

    @property
    def transcript_summary(self) -> summarizer_data_type.TranscriptSummary:
        """Get the transcript summary from the session."""
        if not self.summary:
            raise ValueError("Summary not available")
        try:
            transcript_summary_dict = json.loads(self.summary)["summary"]
            return summarizer_data_type.TranscriptSummary.from_dict(transcript_summary_dict)
        except KeyError:
            raise ValueError("Summary not available")

    @property
    def response_metadata(self) -> dict:
        """Get the response metadata from the session."""
        if not self.session:
            raise ValueError("Response metadata not available")
        try:
            return json.loads(self.session)["response_metadata"]
        except KeyError:
            raise ValueError("Response metadata not available")


class Message(Base):
    __tablename__ = "message_store"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("conversation_sessions.id"), nullable=False)
    # typical message is quite long, and we have to account for worst case
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())

    # Relationship to link back to the ConversationSession
    session = relationship("ConversationSession", back_populates="messages")

    def __repr__(self):
        return f"Message(session_id='{self.session_id}', message='{self.message}', timestamp='{self.timestamp}')"

    def as_transcript_line(self) -> str:
        """Convert a message to a line in a transcript."""

        message_dict = json.loads(self.message)
        message_type = message_dict.get("type", None)
        message_data = message_dict.get("data", None)

        if not message_type or not message_data:
            raise ValueError("Invalid message format")

        if message_type == "ai":
            role = "Doctor"
        elif message_type == "human":
            role = "Patient"
        else:
            role = "Unknown"

        if content := message_data.get("content", None):
            return f"{role}: {content}"

        raise ValueError("Invalid message format")


def create_tables(engine: Engine) -> None:
    Base.metadata.create_all(engine)
