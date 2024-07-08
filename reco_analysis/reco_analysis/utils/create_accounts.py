from reco_analysis.data_model import data_models

session = data_models.get_session()


def create_patient(username: str, first_name: str, last_name: str, email: str, password: str):
    # Test case: Add a new patient and a message
    if (
        patient := session.query(data_models.Patient)
        .filter(data_models.Patient.username == username)
        .first()
    ):
        print(f"Patient with username {username} already exists")
        return patient

    try:
        new_patient = data_models.Patient(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )
        session.add(new_patient)
        session.commit()
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        raise e

    return new_patient


def create_healthcare_provider(first_name: str, last_name: str, email: str, description: str):
    # Test case: Add a new patient and a message
    if (
        healthcare_provider := session.query(data_models.HealthcareProvider)
        .filter(data_models.HealthcareProvider.email == email)
        .first()
    ):
        print(f"Healthcare provider with email {email} already exists")
        return healthcare_provider

    try:
        new_healthcare_provider = data_models.Patient(
            first_name=first_name,
            last_name=last_name,
            email=email,
            description=description,
        )
        session.add(new_healthcare_provider)
        session.commit()
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        raise e

    return new_healthcare_provider
