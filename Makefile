#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = reco_analysis
PYTHON_VERSION = 3.11.7
POETRY_VERSION = 1.8.3
PYTHON_INTERPRETER = python
PEM_FILE = "jupyter-key.pem"
SERVER_USER = "ubuntu"
SERVER_IP = $(shell cat ec2_ip.txt)
SERVER_IP_DASHED = $(shell cat ec2_ip.txt | sed 's/\./-/g')
REGION = "us-west-2"
HOST = "ec2-$(SERVER_IP_DASHED).$(REGION).compute.amazonaws.com"

#################################################################################
# COMMANDS                                                                      #
#################################################################################

SHELL := /bin/bash

diagnose_path:
	@echo "Current PATH: $(PATH)"

## Setup on new system, from a bare Ubuntu machine
.PHONY: new_setup
new_setup:
	# Check if cuda is installed (use nvcc)
	if ! command -v nvcc --version &> /dev/null; then \
		echo "NOTE: CUDA is not installed."; \
	fi

	# Install system dependencies
	sudo apt-get update
	sudo apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
		libreadline-dev libsqlite3-dev wget curl llvm \
		libncurses5-dev libncursesw5-dev xz-utils tk-dev \
		libffi-dev liblzma-dev python3-openssl git

	# Find pyenv first
	if ! command -v pyenv &> /dev/null; then \
		echo "Installing pyenv..."; \
		curl https://pyenv.run | bash; \
		echo 'export PYENV_ROOT="$$HOME/.pyenv"' >> ~/.bashrc; \
		echo 'export PATH="$$HOME/.pyenv/bin:$$PATH"' >> ~/.bashrc; \
		echo 'eval "$$(pyenv init --path)"' >> ~/.bashrc; \
		echo 'eval "$$(pyenv init -)"' >> ~/.bashrc; \
		exec /bin/bash --login; \
	else \
		echo "Pyenv is already installed."; \
	fi

	# Reload the shell configuration
	/bin/bash --login -c "source ~/.bashrc && echo 'Pyenv is installed and configured.'"

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

	# Install jupyterlab
	pip install jupyterlab


## SSH into remote server
.PHONY: ssh
ssh:
	ssh -i ~/.ssh/$(PEM_FILE) $(SERVER_USER)@$(HOST)


## Git clone the project in the remote server
.PHONY: remote_git_clone
remote_git_clone:
	ssh -i ~/.ssh/$(PEM_FILE) $(SERVER_USER)@$(HOST) "\
	git clone https://github.com/recoverycompanion/reco.git"


#################################################################################
# Jupyter Lab Commands - Run these in order									    #
#################################################################################

## Start Jupyter Lab server on remote server (run this on the REMOTE server)
.PHONY: jupyterlab_up
jupyterlab_up:
	# Start Jupyter Lab and log the token
	cd reco_analysis && tmux new-session -d -s jupyterlab 'poetry run jupyter lab --no-browser --port=8888'
	sleep 8
	tmux capture-pane -t jupyterlab -p -S -1000 | tr -d '\n' | grep -oP -m 1 'http://127.0.0.1:8888/lab\?token=\K[a-zA-Z0-9_-]+' | head -n 1 > jupyter_token.log

## Fetch the token file from the remote server (run this on the LOCAL machine)
.PHONY: jupyterlab_fetch_token
jupyterlab_fetch_token:
	scp -i ~/.ssh/$(PEM_FILE) $(SERVER_USER)@$(HOST):~/reco/jupyter_token.log ./jupyter_token.log


## Connect to Jupyter Lab server (from LOCAL machine)
.PHONY: jupyterlab_connect
jupyterlab_connect:
	# Port forward
	ssh -NfL 9999:localhost:8888 -i ~/.ssh/$(PEM_FILE) $(SERVER_USER)@$(HOST)

	# Open browser with the token
	TOKEN=$$(cat jupyter_token.log) && open "http://localhost:9999/?token=$$TOKEN"

## Stop Jupyter Lab server on remote server (run this on REMOTE machine)
.PHONY: jupyterlab_down
jupyterlab_down:
	tmux kill-session -t jupyterlab

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
