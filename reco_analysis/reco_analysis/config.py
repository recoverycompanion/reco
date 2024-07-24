from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file if it exists
load_dotenv()

# Directory paths
PROJ_ROOT = Path(__file__).resolve().parents[1]
logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")

DATA_DIR = PROJ_ROOT / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
SUMMARIES_DIR = DATA_DIR / "summaries"
EVALUATION_DIR = DATA_DIR / "evaluations"
TRANSCRIPTS_EVALUATION_DIR = EVALUATION_DIR / "transcripts"
SUMMARIES_EVALUATION_DIR = EVALUATION_DIR / "summaries"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"