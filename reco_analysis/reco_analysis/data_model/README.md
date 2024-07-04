# Data Model and Database

The RECO Database Schema is designed to support a healthcare application that simulates dialogues between healthcare providers and patients. This schema is implemented using SQLAlchemy ORM, facilitating interactions with a PostgreSQL database. It includes models for Patient, HealthcareProvider, ConversationSession, and Message.

## Project Structure

`models.py`: Contains the SQLAlchemy ORM models.
`init_test_data.py`: Script to populate the database with synthetic test data for development purposes.
`alembic/`: Contains migrations and configuration for Alembic.

## Models

- **`Patient`** - Represents a patient with fields for personal information, linked healthcare provider, and conversation sessions.

- **`HealthcareProvider`** - Represents a healthcare provider who can be linked to multiple patients.

- **`ConversationSession`** - Represents a conversation session linked to a specific patient, capable of storing messages and session summaries.

- **`Message`** - Represents individual messages within a conversation session, linked to the specific session.

## Setup

### Environment Variables

Ensure that your `.env` file is set up properly in the project root for all `POSTGRES_DB_*` variables. Please see `.env.example` for reference.

To toggle between development and production environments, set the `POSTGRES_DB_ENVIRONMENT` variable to `DEV` or `PROD` prior to running any database-related commands. For example:

```sh
POSTGRES_DB_ENVIRONMENT=DEV poetry run python init_test_data.py
```

### Makefile Commands

Use the provided Makefile commands to create and configure the database, and manage database schema migrations using Alembic.

```sh
# Database Setup
make create_dev_db  # Create and initialize the development database on MacOS.
make create_prod_db  # Setup the production database on Linux.

# Alembic Migrations (translation: this is how we create tables and manage schema changes)
make alembic_migrate message="describe your changes"  # Generates a new Alembic migration.
make alembic_upgrade  # Upgrade the database to the latest migration.
make alembic_downgrade  # Rollback the database by one migration.
make alembic_current  # Show the current revision of the database.
```

For all `alembic_*` commands, you can specify the environment using the `env` argument, e.g., `make alembic_upgrade env=DEV`. The `env` argument defaults to `DEV`. Valid values are `DEV` and `PROD`.

### New Setup for Dev Environment

```sh
# Install dependencies
poetry install

# Create and initialize the development database (this will also run the Alembic migrations and add fake test data)
make create_dev_db
```

## Development Workflow

1. Define/modify the models in `data_models.py`.
2. Create a new Alembic migration using the Makefile command `make alembic_migrate message="describe your changes"`.
   - Double-check the migration script generated in the `alembic/versions` directory to ensure that the changes are correct; modify if necessary.
3. Apply the migration to the database using `make alembic_upgrade`.
   - You don't need this, but you can specify the environment using `env`, e.g., `make alembic_upgrade env=DEV`. `env` defaults to `DEV` anyways.
4. If necessary, rollback the migration using `make alembic_downgrade env=DEV`.
5. Test the changes by running the application or querying the database.
6. After tests are complete and code is ready for production, apply the migration to the production database using `make alembic_upgrade env=PROD`.
