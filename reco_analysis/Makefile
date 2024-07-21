#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = reco_analysis
PYTHON_VERSION = 3.11.7
POETRY_VERSION = 1.8.3
PYTHON_INTERPRETER = python
S3_BUCKET = s3://reco
PROFILE = default

#################################################################################
# COMMANDS                                                                      #
#################################################################################


## Install Python and its dependencies
.PHONY: install
install:
	# Check if Python 3.11.7 is installed, and install it if not
	if ! pyenv versions --bare | grep -q $(PYTHON_VERSION); then \
		echo "Python $(PYTHON_VERSION) is not installed. Installing..."; \
		pyenv install $(PYTHON_VERSION); \
	fi

	# Switch to the specified Python version
	pyenv global $(PYTHON_VERSION)

	# Ensure pip is upgraded
	python -m pip install --upgrade pip

	# Check if Poetry is installed and its version
	@if command -v poetry &> /dev/null; then \
		CURRENT_VERSION=$$(poetry --version | sed -E 's/[^0-9.]*([0-9.]+).*/\1/'); \
		if [ "$$CURRENT_VERSION" != "$(POETRY_VERSION)" ]; then \
			echo "Poetry version is $$CURRENT_VERSION. Installing Poetry $(POETRY_VERSION)..."; \
			pip install --force-reinstall poetry==$(POETRY_VERSION); \
		else \
			echo "Poetry $(POETRY_VERSION) is already installed."; \
		fi \
	else \
		echo "Poetry is not installed. Installing Poetry $(POETRY_VERSION)..."; \
		pip install poetry==$(POETRY_VERSION); \
	fi

	# Install dependencies
	poetry install


## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8 and black (use `make format` to do formatting)
.PHONY: lint
lint:
	poetry run flake8 reco_analysis
	poetry run isort --check --diff --profile black reco_analysis
	poetry run black --check --config pyproject.toml reco_analysis

## Format source code with black and isort
.PHONY: format
format:
	poetry run black --config pyproject.toml reco_analysis
	poetry run isort --profile black reco_analysis


## Download Data from S3
.PHONY: sync_data_down
sync_data_down:
	poetry run aws s3 sync $(S3_BUCKET)/data/ data/ --profile $(PROFILE)


## Upload Data to S3
.PHONY: sync_data_up
sync_data_up:
	poetry run aws s3 sync data/ $(S3_BUCKET)/data/ --profile $(PROFILE)

aws_configure:
	# only configure if not already configured
	@if ! aws configure --profile $(PROFILE) list; then \
		aws configure --profile $(PROFILE); \
	fi

## Alembic - Create a new migration
.PHONY: alembic_migrate
alembic_migrate:
	POSTGRES_DB_ENVIRONMENT=$(env) cd reco_analysis/data_model && poetry run alembic revision --autogenerate -m "$(message)"


env ?= DEV

## Alembic - Upgrade to the latest migration
.PHONY: alembic_upgrade
alembic_upgrade:
	POSTGRES_DB_ENVIRONMENT=$(env) cd reco_analysis/data_model && poetry run alembic upgrade head

## Alembic - Downgrade to the previous migration
.PHONY: alembic_downgrade
alembic_downgrade:
	POSTGRES_DB_ENVIRONMENT=$(env) cd reco_analysis/data_model && poetry run alembic downgrade -1

## Alembic - Show the current revision
.PHONY: alembic_current
alembic_current:
	POSTGRES_DB_ENVIRONMENT=$(env) cd reco_analysis/data_model && poetry run alembic current


## Create local dev postgres database from scratch (MacOS)
.PHONY: create_dev_db
create_dev_db:
	# ensure that postgres is running
	brew services start postgresql
	# first, drop the database if it exists
	psql -c "DROP DATABASE IF EXISTS reco" postgres
	# create the database
	createdb reco
	# create the tables using alembic_upgrade
	make alembic_upgrade env=DEV
	# add fake data
	POSTGRES_DB_ENVIRONMENT=DEV poetry run python reco_analysis/data_model/init_test_data.py

## Delete local dev postgres database (local dev only)
.PHONY: delete_dev_db
delete_dev_db:
	# first, drop the database if it exists
	psql -c "DROP DATABASE IF EXISTS reco" postgres

## Create prod postgres database from scratch (Linux)
.PHONY: create_prod_db
create_prod_db:
	# first, drop the database if it exists
	psql -c "DROP DATABASE IF EXISTS reco" postgres
	# create the database
	createdb reco
	# create the tables using alembic_upgrade
	make alembic_upgrade env=PROD

## Streamlit - start app. Set either `env=DEV` (default) or `env=PROD`
.PHONY: chatbot_app_up
chatbot_app_up:
	POSTGRES_DB_ENVIRONMENT=$(env) poetry run streamlit run reco_analysis/chatbot_app/streamlit_app.py

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

# .PHONY: data
# data: install
# 	$(PYTHON_INTERPRETER) reco_analysis/data/make_dataset.py


#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

## Show this help
.PHONY: help
help:
	@python -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
