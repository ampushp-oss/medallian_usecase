import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEFAULT_INPUT_DIR = BASE_DIR / "data" / "raw"
DEFAULT_OUTPUT_DIR = BASE_DIR / "warehouse"
DEFAULT_MODEL = os.getenv("MODEL_NAME", "claude-3-5-sonnet-20241022")
DEFAULT_API_KEY = os.getenv("ANTHROPIC_API_KEY")
