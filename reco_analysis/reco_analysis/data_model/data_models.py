import os
import uuid

from dotenv import load_dotenv
from sqlalchemy import (
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
from sqlalchemy.orm import relationship

env_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(env_file_path)

USER = "reco_admin"
PASSWORD = os.getenv("POSTGRES_DB_PASSWORD") or "averysecurepasswordthatyouwillneverguess"
HOST = os.getenv("POSTGRES_DB_HOST") or "localhost"
PORT = os.getenv("POSTGRES_DB_PORT") or "5432"
DB = os.getenv("POSTGRES_DB_NAME") or "reco"
DB_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"


def get_engine(db_url: str) -> "Engine":
    return create_engine(db_url)


Base = declarative_base()


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)
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

    def __repr__(self):
        return (
            f"Patient(username='{self.username}', first_name='{self.first_name}', "
            f"last_name='{self.last_name}', email='{self.email}', "
            f"created_at='{self.created_at}', updated_at='{self.updated_at}')"
        )

    def new_session(self, summary: str | None = None) -> "ConversationSession":
        return ConversationSession(patient_id=self.id, summary=summary)


class HealthcareProvider(Base):
    __tablename__ = "healthcare_providers"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    email = Column(String(120), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    patients = relationship("Patient", back_populates="healthcare_provider", uselist=True)

    def __repr__(self):
        return (
            f"HealthcareProvider(first_name='{self.first_name}', last_name='{self.last_name}', "
            f"email='{self.email}', created_at='{self.created_at}', updated_at='{self.updated_at}')"
        )


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

    def __repr__(self):
        return (
            f"ConversationSession(patient_id='{self.patient_id}', created_at='{self.created_at}', "
            f"updated_at='{self.updated_at}', summary='{self.summary}')"
        )


class Message(Base):
    __tablename__ = "message_store"

    id = Column(Integer, primary_key=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("conversation_sessions.id"), nullable=False)
    # typical message is quite long, and we have to account for worst case
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())

    # Relationship to link back to the ConversationSession
    session = relationship("ConversationSession", back_populates="messages")

    def __repr__(self):
        return f"Message(session_id='{self.session_id}', message='{self.message}', timestamp='{self.timestamp}')"


def create_tables(engine: Engine) -> None:
    Base.metadata.create_all(engine)
