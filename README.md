# RECO: Recovery Companion

![RECO logo](reco_analysis/docs/reco_logo.jpeg)

[_Visit our website!_](https://recoverycompanion.github.io/reco/)

___Monitoring patients with heart failure on their recovery journey.___

RECO is a conversational AI app that assists patients with heart failure (HF) who have recently been discharged from the hospital. HF is a condition where the heart struggles to pump blood efficiently, often due to damage or disease affecting the heart's muscle. Patients frequently face worsened symptoms soon after hospital discharge, which if not addressed swiftly, can lead to rehospitalization.

Our conversational AI aims to monitor these patients by routinely asking about their symptoms, vital signs, and medication adherence. It will then compile this information and summarize findings in a structured PDF report for their physician. This proactive approach helps in detecting any worsening of the condition early, potentially prompting timely medical interventions.

The conversational AI is not designed to diagnose conditions or offer medical advice directly to patients but serves as a crucial communication bridge between patients and their healthcare providers.

The project has the following key impacts:

- __Enhanced Decision-Making__: Doctors receive concise daily summaries, facilitating quicker and better-informed clinical decisions.
- __Scalability__: The system allows for the management of larger patient volumes without overburdening healthcare providers.
- __Patient Engagement__: Studies show and patients agree -- the chatbot is easier and more straightforward than traditional forms.

If you would like a live demo, please reach out to <reco.recovery.companion@gmail.com>.

## Application Features

This applications has the following features:

1. __Streamlit-based Conversational AI__: A conversational AI interface that asks patients about their symptoms, vital signs, and medication adherence.
2. __Conversation Session Summarization and Report__: At the end of each session, the app generates a structured PDF report containing organized sections of the patients' symptoms, vital signs, medications, as well as a brief summary of the conversation.
3. __Data Management__: All conversations and summaries are managed per patient in a PostgreSQL database.
4. __LLM Validation__: The underlying LLMs used in the conversational AI and summarization engine are validated using LLM-as-a-Judge methodology.

## Setup, Installation, and Usage

To run the application locally, please follow all instructions under "Initial Setup" and "Spinning up the Streamlit App". This assumes that the repo is already cloned to your local machine.

### Initial Setup

This part takes about 30-60 minutes.

#### Python Dependencies

This project uses Poetry to manage Python packages and dependencies. It’s best to make sure you are not already using a virtual environment, especially when installing poetry. Poetry will manage your environment for you.

```{bash}
pip install poetry
```

> __Note:__ If you’re using Anaconda, you can check your environments using `conda info --envs`. To deactivate an Anaconda environment, use `conda deactivate` To install poetry on your machine, follow [these instructions](https://python-poetry.org/docs/) (installation command is `pipx install poetry`).

After installing poetry, run the following to install the project dependencies.

```{bash}
cd reco_analysis
make install
```

#### Setting up the Database

To set up the database, please install postgresql on your machine first:

```{bash}
brew install postgresql
```

Then, create a new user and database:

```{bash}
# Create a new user. Change the password to something more secure if needed.
psql postgres -c "CREATE ROLE reco_admin WITH LOGIN PASSWORD 'averysecurepasswordthatyouwillneverguess';"
psql postgres -c "ALTER ROLE reco_admin CREATEDB;"

# Create a new database
cd reco_analysis  # if not already in the reco_analysis directory
make create_dev_db
```

After this step, make a copy of the `.env.example` file and rename it to `.env`. Modify `POSTGRES_DB_DEV_PASSWORD` and any other variables as needed. This is how the app will connect to the database.

#### Setting up OpenAI API Key

RECO is an LLM-based application, and fundamentally uses OpenAI's GPT models (GPT 4o and GPT 4o-mini). As such, you will need to set up an OpenAI API key to run the application. Assuming you already have an OpenAI account, you can find/create your API key in the [API Keys dashboard](https://platform.openai.com/api-keys). Once you have your API key, add it to the `.env` file in `OPENAI_API_KEY` and `OPEN_ORG_ID` variables.

#### Setting up "Post Office"

The `post_office.py` module (cute name) is a module in our summarization engine part of RECO that sends out the PDF reports to the patients' healthcare providers. To set up the email server, you will need to add the following variables to the `.env` file: `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`. Because of the variety of email servers, we do not provide further instructions on how to set up the email server, but most generic, non-business Gmail accounts should work (search online for details).

### Spinning up the Streamlit App

Here's how you can simply run the Streamlit app:

```{bash}
cd reco_analysis  # if you're not already in the reco_analysis directory
make chatbot_app_up env=DEV
```

This will start the Streamlit app on your local machine. You can access it by navigating to `http://localhost:8501` in your browser.

## Development

### Managing Dependencies

Dependencies are managed in the `pyproject.toml` file, which contains all package requirements for our project.

To add new packages/dependencies, please add it to `pyproject.toml` via poetry commands.

To activate a shell with all the requirements met, run `poetry shell`. Note that activating a shell is not necessary to run the app.

### Contributing to RECO

Contributions to the project are welcome. Please make a pull request and tag any of the authors listed below for a review.

This project's license can be found in the [LICENSE](reco_analysis/LICENSE) file.

## Authors

RECO is a capstone project developed by a team of us at the University of California, Berkeley as part of our Master of Information and Data Science program. The team members are:

- Mike Khor - <mike.khor@berkeley.edu>
- Annie Friar - <anniefriar@berkeley.edu>
- Farid Gholitabar - <farid.gholitabar@berkeley.edu>
- Gary Kong - <garykong@berkeley.edu>

## Acknowledgments

We would like to thank our course instructors (Professors Joyce Schen, Zona Kostic), the University of California Berkeley School of Information, and all those who provided invaluable feedback and support throughout the project.

## Contact

For any inquiries or suggestions, you can reach out by creating an issue in the GitHub repository, or by emailing <reco.recovery.companion@gmail.com> or any of the authors' emails.
