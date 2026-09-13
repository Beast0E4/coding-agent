import re
import os
import sys
import time
import shlex
import subprocess

from langchain.tools import tool

from config.config import get_work_directory
from tools.jobs import now_iso, register, BackgroundJob, read_log_tail, stop_pid, all_jobs, is_alive

MAX_OUTPUT_CHARS = 8000
DEFAULT_TIMEOUT = 30

BLOCKED_COMMAND_PATTERNS = (
    # Unix / macOS / Linux
    r"\bsudo\b",
    r"\brm\s+[-a-zA-Z]+f\b",
    r"\bmkfs\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r":\(\)\s*\{",
    r"\bdd\s+if=",
    r"curl\s+[-|]*\s*\|\s*(ba)?sh",
    r"wget\s+[-|]*\s*\|\s*(ba)?sh",
    r"\bchmod\s+777\b",

    # Windows CMD
    r"\bdel(?:ete)?\b",
    r"\berase\b",
    r"\brmdir\b",
    r"\brd\b",
    r"\bformat(?:\.com)?\b",
    r"\bdiskpart\b",
    r"\bshutdown\s+/[sr]\b",

    # Windows PowerShell
    r"\bRemove-Item\b",
    r"\bStop-Computer\b",
    r"\bRestart-Computer\b",
    r"\bClear-Disk\b",
    r"\bFormat-Volume\b",
    r"\bRemove-Partition\b",
    r"\bInitialize-Disk\b",

    # Windows privilege / permission manipulation
    r"\btakeown\.exe\b",
    r"\bicacls\.exe\b",
)

SERVER_PATTERNS = (
    r"\bflask(\s+--app)?\s+run\b",
    r"\buvicorn\b",
    r"\bgunicorn\b",
    r"\bhypercorn\b",
    r"\bpython[0-9.]*\s+\S+app\.py\b",
    r"\bnpm\s+start\b",
    r"\bnpx\s+(serve|next|vite|nuxt)\b",
    r"\bstreamlit\s+run\b",
)

_PIP_PREFIX = re.compile (
    r"^(?:pip[0-9.]*|python[0-9.]*\s+-m\s+pip)\b",
    re.IGNORECASE,
)

_PYTHON_PREFIX = re.compile (r"^python[0-9.]*\b", re.IGNORECASE)

_FLASK_PREFIX = re.compile (r"^flask\b", re.IGNORECASE)

def deny_command (command: str) -> str | None:
    stripped = command.strip ()
    if not stripped:
        return f"Blocked by middleware: empty command"
    
    for pattern in BLOCKED_COMMAND_PATTERNS:
        if re.search (pattern, command, flags=re.IGNORECASE):
            return f"Blocked by middleware: command matched a dangerous pattern - {pattern}"
    
    return None

def looks_like_server (command: str) -> bool:
    return any (re.search (pattern, command, flags=re.IGNORECASE) for pattern in SERVER_PATTERNS)

def rewrite_command (command: str) -> str:
    exe = shlex.quote (sys.executable)
    
    stripped = command.strip ()
    
    if _PIP_PREFIX.match (stripped):
        return _PIP_PREFIX.sub (f"{exe} -m pip", stripped, count=1)
    
    if _PYTHON_PREFIX.match (stripped):
        return _PYTHON_PREFIX.sub (exe, stripped, count=1)
    
    if _FLASK_PREFIX.match (stripped):
        return _FLASK_PREFIX.sub (f"{exe} -m flask", stripped, count=1)
    
    return command

def clip (text: str) -> str:
    if len (text) <= MAX_OUTPUT_CHARS:
        return text
    
    return text[:MAX_OUTPUT_CHARS] + "\n...(truncated)"

def run_foreground (command: str, timeout: int) -> str:
    cwd = get_work_directory ()
    cwd.mkdir (parents=True, exist_ok=True)
    
    env = os.environ.copy ()
    env.setdefault ("PYTHONUNBUFFERED", "1")
    
    try:
        completed = subprocess.run (
            ["/bin/bash", "-lc", command],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout
        )
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or "") + (e.stderr or "")
        return (
            f"Timedout after {timeout} sec: Process killed"
            "If this is a server, rerun with background=true"
            f"{clip (str (stdout))}"
        )
        
    chunks = []
    if completed.stdout:
        chunks.append (completed.stdout.rstrip ())
    if completed.stderr:
        chunks.append (completed.stderr.rstrip ())
        
    body = "\n".join (chunks) if chunks else "No output"
    return f"exit_code={completed.returncode}\ncwd={cwd}\n_{clip (body)}"

def run_background (command: str, timeout: int) -> str:
    cwd = get_work_directory ()
    cwd.mkdir (parents=True, exist_ok=True)
    
    env = os.environ.copy ()
    env.setdefault ("PYTHONUNBUFFERED", "1")
    
    log_dir = cwd / ".agent_jobs"
    log_dir.mkdir (parents=True, exist_ok=True)
    
    stamp = now_iso ().replace (":", "").replace ("+", "")
    tmp_log = log_dir / f"pending-{stamp}.log"
    log_file = tmp_log.open ("w", encoding="utf-8")
    
    try:
        proc = subprocess.Popen (
            ["/bin/bash", "-lc", command],
            cwd=cwd,
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
    finally:
        log_file.close ()
    
    
    log_path = log_dir / f"{proc.pid}.log"
    tmp_log.rename (log_path)
    register (
        BackgroundJob (
            pid=proc.pid,
            command=command,
            log_path=log_path,
            started_at=now_iso (),
            proc=proc
        )
    )
    
    time.sleep (1)
    tail = read_log_tail (log_path)
    if proc.poll () is not None:
        stop_pid (proc.pid)
        return (
            f"Background command exited immediately (pid = {proc.pid})"
            f"exit_code={proc.returncode}.\n{clip (tail)}"
        )
    
    urls = re.findall (r"https?://[^\s]+", tail)
    url_line = f"Open in the brower: {urls[0]} \n" if urls else (
        "No url in the log yet - try http://127.0.0.1:3000"
        "and check list_jobs if it is blank.\n"
    )
    
    return (
        f"{url_line}\n"
        f"Started background job pid = {proc.pid}\n"
        f"Log: {log_path}\n"
        f"cwd = {cwd}"
        f"Use list_jobs/stop_jobs to manage it.\n"
        f"----------- OUTPUT SO FAR ----------- \n{clip (tail)}"
    )
    
@tool
def stop_job (pid: int) -> str:
    """
    Stop a background job previously started by run_command
    Args:
        pid: The process id of the job to stop
    """
    return stop_pid (pid)

@tool
def run_command (command: str, background: bool = False, timeout_seconds: int = 0) -> str:
    """
    Run a bash command in the working directory (host machine, not sandbox)
    
    Foreground wait for completion. Set background=True for servers like (flask, uvicorn, npm start)
    so they keep running. Server-like commands are auto backgrounded even if you forget the flag.
    
    Args:
        command: the bash command to run, e.g. 'python app.py'
        background: If true, start the process and return the pid immediately
        timeout_seconds: Maximum time to wait for the command to complete. This is for foreground timeout. 0 uses default (30s)
    """
    
    blocked = deny_command (command)
    if blocked :
        return blocked
    
    timeout = timeout_seconds if timeout_seconds > 0 else DEFAULT_TIMEOUT
    background = bool (background) or looks_like_server (command)
    
    command = rewrite_command (command)
    
    if background:
        return run_background (command)
    else:
        return run_foreground (command, timeout)

@tool
def list_jobs () -> str:
    """
    List background process started with run_command (servers, long jobs)
    """
    
    jobs = all_jobs ()
    if not jobs:
        return "No background jobs running"
    
    lines = []
    for job in jobs:
        state = "running" if is_alive (job.pid) else "exited"
        lines.append (
            f"pid={job.pid} state={state} started={job.started_at} cmd={job.command}"
        )
        tail = read_log_tail (job.log_path, max_chars=800)
        
        if tail:
            lines.append (tail.rstrip ())
            lines.append ("-----------------")
        
        return "\n".join (lines)