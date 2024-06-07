#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = reco_analysis
PYTHON_VERSION = 3.11
PYTHON_INTERPRETER = python
S3_BUCKET = s3://reco
PROFILE = default

#################################################################################
# COMMANDS                                                                      #
#################################################################################


## Install Python Dependencies
.PHONY: install
install:
	pip install --upgrade pip
	poetry --version || pip install poetry==1.8.3
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
