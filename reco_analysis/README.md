# RECO Analysis

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

RECO: Recovery Companion, to monitor patients with heart failure on their recovery journey

## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for reco_analysis
│                         and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── reco_analysis      <- Source code for use in this project.
```

--------

## First-time setup

The following installs python 3.11.7 and poetry 1.8.3, if not already installed, as well as the project dependencies, including dev dependencies like AWS CLI.

```{bash}
make install
```

Then, configure AWS CLI:

```{bash}
make aws_configure
```

Then enter your AWS credentials as follows:

- AWS Access Key ID [None]: copy this from lastpass note
- AWS Secret Access Key [None]: copy this from lastpass note
- Default region name [None]: `us-west-2`
- Default output format [None]: `json`

## Syncing data

```{bash}
make sync_data_down  # to download data
```

```{bash}
make sync_data_up  # to upload data
```
