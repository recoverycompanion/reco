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


## Setup on new system, from a bare Ubuntu machine
.PHONY: new_setup
new_setup:
	# Check if cuda is installed (use nvcc)
	if ! command -v nvcc --version &> /dev/null; then \
		echo "NOTE: CUDA is not installed."; \
	fi

	# Install system dependencies
	sudo apt-get update

	# Find pyenv first
	if ! command -v pyenv &> /dev/null; then \
		sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev; \
		curl https://pyenv.run | bash; \
		echo 'export PATH="$$HOME/.pyenv/bin:$$PATH"' >> ~/.bashrc; \
		echo 'eval "$$(pyenv init --path)"' >> ~/.bashrc; \
		echo 'eval "$$(pyenv init -)"' >> ~/.bashrc; \
		source ~/.bashrc; \
	fi

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


## Start Jupyter Lab server (from remote server like EC2)
.PHONY: jupyterlab_up
jupyterlab_up:
	# Start Jupyter Lab and log the token
	ssh -i ~/.ssh/$(PEM_FILE) $(SERVER_USER)@$(HOST) "\
	tmux new-session -d -s jupyterlab 'jupyter lab --no-browser --port=8888' && \
	sleep 5 && \
	tmux capture-pane -t jupyterlab -p -S -1000 | grep -oP 'http://127.0.0.1:8888/\K.*' > jupyter_token.log"

	# Fetch the token file from the remote server
	scp -i ~/.ssh/$(PEM_FILE) $(SERVER_USER)@$(HOST):jupyter_token.log ./jupyter_token.log


## Connect to Jupyter Lab server (from local machine)
.PHONY: jupyterlab_connect
jupyterlab_connect:
	# Port forward
	ssh -NfL 9999:localhost:8888 -i ~/.ssh/$(PEM_FILE) $(SERVER_USER)@$(HOST)

	# Open browser with the token
	TOKEN=$$(cat jupyter_token.log) && open "http://localhost:9999/?token=$$TOKEN"


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
