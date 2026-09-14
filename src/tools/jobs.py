import os
import contextlib
import subprocess
from dataclasses import dataclass, field
from typing import Any
from pathlib import Path
from datetime import datetime, UTC

@dataclass
class BackgroundJob:
    pid: int
    command: str
    started_at: str
    log_path: str
    proc: Any = field(default=None, repr=False)

_JOBS: dict[int, BackgroundJob] = {}

def register(job: BackgroundJob) -> None:
    _JOBS[job.pid] = job

def get(pid: int) -> BackgroundJob | None:
    return _JOBS.get(pid)

def all_jobs() -> list[BackgroundJob]:
    return list(_JOBS.values())

def remove(pid: int) -> BackgroundJob | None:
    return _JOBS.pop(pid, None)

def is_alive(pid: int) -> bool:
    job = get(pid)
    
    if job is not None and job.proc is not None:
        return job.proc.poll() is None
    
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def stop_pid(pid: int) -> str:
    job = get(pid)
    
    if job is None:
        return f"Error: {pid} is not a job started by this agent"
    
    if not is_alive(pid):
        if job.proc is None:
            with contextlib.suppress(ChildProcessError):
                job.proc.wait(timeout=0.1)
                
        remove(pid)
        return f"Job {pid} is already stopped"
    
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
    
    if job.proc is not None:
        with contextlib.suppress(subprocess.TimeoutExpired):
            job.proc.wait(timeout=1.5)
            
    remove(pid)
    command_name = job.command if job else "Unknown command"
    return f"Job {pid} created by {command_name} is stopped"

def read_log_tail(log_path: Path, *, max_chars: int = 4000) -> str:
    if not log_path.exists:
        return ""
    
    text = log_path.read_text(encoding='utf-8', errors="replace")
    
    if len(text) > max_chars:
        return text[-max_chars:]
    
    return text

def now_iso() -> str:
    return datetime.now(UTC).isoformat()