import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv ()

PROJECT_ROOT = Path(__file__).resolve ().parent.parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
WORK_DIR = PROJECT_ROOT / "workspace"

AGENT_NAME = "Coding_Agent"

MAX_MODEL_RUNS_PER_RUN = int (os.getenv ("MAX_MODEL_RUNS_PER_RUN", "10"))

MAX_READ_BYTES = int (os.getenv ("MAX_READ_BYTES", "1000000"))

def hitl_enabled () -> bool:
    return os.getenv ("HITL_ENABLED", "true").lower () in {"1", "yes", "true"}

def get_work_directory () -> Path:
    override = os.getenv ("WORK_DIR", "").strip ()
    
    if override:
        return Path (override).expanduser ().resolve ()
    
    return WORK_DIR.resolve ()