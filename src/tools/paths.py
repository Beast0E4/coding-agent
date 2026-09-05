from fnmatch import fnmatch
from pathlib import Path
from config.config import get_work_directory

BLOCKED_PATH_PATTERNS = [
    ".env",
    ".env.*",
    ".pem",
    ".key",
    ".secret",
    ".git",
    ".git/**",
    "*.log",
    "*.p12"
]

def normalise_path (path : str) -> str:
    normalised = Path (path).as_posix ()
    
    if normalised.startswith ("./"):
        normalised = normalised[2:]
    
    return normalised

def is_blocked (path: str) -> bool:
    normalised = normalise_path (path)
    return any (fnmatch (normalised, pattern) for pattern in BLOCKED_PATH_PATTERNS)

def resolve_work_path (path : str) -> Path:
    work_dir = get_work_directory ()
    work_dir.mkdir (parents=True, exist_ok=True)
    candidate = (work_dir / path).resolve ()
    
    try :
        candidate.relative_to (work_dir)
    except ValueError:
        raise ValueError (f"Path escapes working directory: {path}")
    return candidate