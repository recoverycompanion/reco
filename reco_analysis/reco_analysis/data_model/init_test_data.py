import datetime
import random
import typing

from sqlalchemy.orm import sessionmaker

from reco_analysis.data_model.data_models import (
    ConversationSession,
    HealthcareProvider,
    Message,
    Patient,
    get_engine,
)

# Establish a database session
engine = get_engine()
Session = sessionmaker(bind=engine)
session = Session()

# Sample data pools
first_names = ["John", "Jane", "Sam", "Olivia", "Dave"]
last_names = ["Doe", "Smith", "Brown", "Wilson", "Taylor"]
domains = ["example.com", "demo.org", "sample.net"]

chosen_names = []

start_time = datetime.datetime.now() - datetime.timedelta(days=30)
time_passed = datetime.timedelta(minutes=5)


def create_email(name):
    domain = random.choice(domains)
    return f"{name.lower()}@{domain}"


def create_name() -> typing.Tuple[str, str]:
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)

    if (first_name, last_name) in chosen_names:
        return create_name()
    chosen_names.append((first_name, last_name))
    return first_name, last_name


def create_healthcare_providers(count=5):
    for _ in range(count):
        first_name, last_name = create_name()
        provider = HealthcareProvider(
            first_name=first_name,
            last_name=last_name,
            email=create_email(f"{first_name}.{last_name}"),
            description="A dedicated healthcare professional.",
            created_at=start_time,
        )
        session.add(provider)
    session.commit()


def create_patients(count=10):
    providers = session.query(HealthcareProvider).all()
    for _ in range(count):
        first_name, last_name = create_name()
        patient = Patient(
            username=f"{first_name.lower()}{random.randint(10, 99)}",
            first_name=first_name,
            last_name=last_name,
            email=create_email(f"{first_name}{last_name}"),
            password="securepassword123",
            healthcare_provider=random.choice(providers),
            created_at=start_time,
        )
        session.add(patient)
    session.commit()


def create_sessions(count=20):
    global time_passed

    patients = session.query(Patient).all()
    for _ in range(count):
        session_record = ConversationSession(
            patient=random.choice(patients),
            summary="Summary of the session discussing general health.",
            created_at=start_time + time_passed,
        )
        time_passed += datetime.timedelta(minutes=5)
        session.add(session_record)
    session.commit()


def create_messages(count=50):
    global time_passed

    sessions = session.query(ConversationSession).all()
    for _ in range(count):
        message = Message(
            session=random.choice(sessions),
            message="This is a generated message reflecting patient interaction.",
            timestamp=start_time + time_passed,
        )
        time_passed += datetime.timedelta(minutes=5)
        session.add(message)
    session.commit()


if __name__ == "__main__":
    random.seed(42)
    create_healthcare_providers()
    create_patients()
    create_sessions()
    create_messages()
