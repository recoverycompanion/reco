# RECO: Recovery Companion

*Monitoring patients with heart failure on their recovery journey.*

We're developing a chatbot that assists patients with heart failure (HF) who have recently been discharged from the hospital. HF is a condition where the heart struggles to pump blood efficiently, often due to damage or disease affecting the heart's muscle. Patients frequently face worsened symptoms soon after hospital discharge, which if not addressed swiftly, can lead to rehospitalization.

Our chatbot aims to monitor these patients by routinely asking about their symptoms, vital signs, and medication adherence. It will then compile this information into a structured report for their physician. This proactive approach helps in detecting any worsening of the condition early, potentially prompting timely medical interventions. The chatbot is not designed to diagnose conditions or offer medical advice directly to patients but serves as a crucial communication bridge between patients and their healthcare providers.

EVERYTHING BELOW IS GENERIC AND WILL BE FILLED OUT:

## Installation

Provide detailed instructions on how to install the project, covering any prerequisites, dependencies, and environmental setup.

```{bash}
git clone https://github.com/yourusername/yourprojectname.git
cd yourprojectname
pip install -r requirements.txt
```

## Package Management

###Poetry Overview

Poetry is a tool that helps us manage Python packages and dependencies seamlessly across our team.

###Initial Setup

First, it’s best to make sure you are not already using a virtual environment, especially when installing poetry. Poetry will manage your environment for you. If you’re using Anaconda, you can check your environments using `conda info --envs`. To deactivate an Anaconda environment, use `conda deactivate` To install poetry on your machine, follow [these instructions](https://python-poetry.org/docs/) (installation command is `pipx install poetry`).

###Managing Dependencies

Dependencies are managed in the all important pyproject.toml file, which contains the package requirements for our project. If we need another package as we continue working on it, we add it to the pyproject.toml as a requirement. To ensure you have the proper packages for our app, once poetry is installed, navigate to the reco-analysis folder of our repo. In this folder, run `poetry update`. This will have you add the packages needed for our project. To activate a shell with all the requirements met, run `poetry shell`.


## Usage

A few snippets showing the simplest use case for your project. This section can include code blocks or CLI commands:

```{python}
import yourpackage
```

```{python}
# Example of using your project
result = yourpackage.do_something()
print(result)
```

```{bash}s
# Command-line example
yourcommand --option arg
```

## Features

Highlight the key features of your project. What makes it stand out?

Feature 1
Feature 2
Feature 3


## Contributing

State if you are open to contributions and what your requirements are for accepting them.

## Fork the Project

Create your Feature Branch (git checkout -b feature/AmazingFeature)
Commit your Changes (git commit -m 'Add some AmazingFeature')
Push to the Branch (git push origin feature/AmazingFeature)
Open a Pull Request
License
Distribute your project under the License. For example:

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE) file for details

## Authors

Your Name - Initial work - YourUsername
See also the list of contributors who participated in this project.

## Acknowledgments

Hat tip to anyone whose code was used
Inspiration
etc.

## Contact

For any inquiries, you can reach out by creating an issue in the GitHub repository or directly through your preferred method of contact.
