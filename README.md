# Coding Agent (MVP - 1)

The Coding Agent is an interactive, locally-running AI coding assistant built using LangChain and LangGraph. The agent reads, lists, and writes real files to a designated workspace directory and executes shell commands and background servers on the host machine. It features a robust middleware stack that enforces model-call limits, generates comprehensive audit logs, applies payload guardrails, and requires Human-in-the-Loop (HITL) execution for state-changing actions.

This documentation covers the architecture, configuration, and security guardrails for the project referenced in the file beast0e4/coding-agent.

## Key Features

* **File Operations:** The agent can safely read, edit, list, and write text files across various programming languages directly to the workspace directory.


* **Command Execution:** Capable of running shell commands in the foreground or spawning long-running background tasks, such as Flask, Uvicorn, or Node servers.


* **Human-In-The-Loop (HITL):** When enabled, intercepts execution and prompts the user for approval via the CLI before authorizing tools like `run_command`, `write_file`, and `edit_file`.


* **Audit Logging:** Appends a JSON-formatted log entry of all tool executions, arguments, and result previews to `agent_audit.log` for full traceability.


* **Structured Outputs:** Emits a `TurnSummary` containing a concise summary of actions, a list of touched file paths, and the current operational status (`ok`, `needs_input`, or `failed`).


* **Prompt Templating:** Uses Jinja templates for the system prompt and greeting message, making the agent's behavior easily configurable without modifying Python code.



## Project Structure

The project relies on Python 3.11 and utilizes `pyproject.toml` and `uv.lock` for package management.

* `src/main.py`: The primary entry point containing the interactive CLI chat loop and HITL prompt logic.


* `src/agent.py`: Handles agent instantiation, binding the language model, tools, prompt templates, and middlewares.


* `src/config/config.py`: Manages environment configuration and constant definitions.


* `src/middlewares/`: Houses security and operational interceptors, including `audit.py`, `hitl.py`, and `protection.py`.


* `src/tools/`: Includes all modular capabilities such as `edit_file.py`, `jobs.py`, `list_files.py`, `read_file.py`, `shell.py`, and `write_file.py`.


* `prompts/`: Contains Jinja templates (`greeting.jinja` and `system.jinja`) used to define the agent's system instructions and greeting.



## Agent Capabilities

The agent accesses a comprehensive tool catalog to interact with the environment.

| Tool | Description |
| --- | --- |
| **`write_file`** | Creates or overwrites a UTF-8 text file on disk using real line breaks instead of markdown fences. |
| **`edit_file`** | Replaces exact string matches within a target file, primarily used for small, precise modifications. |
| **`read_file`** | Reads the contents of a UTF-8 text file from the working directory. |
| **`list_files`** | Recursively lists files and directories under a specified path within the workspace. |
| **`run_command`** | Executes a bash command in the host machine's working directory, with support for backgrounding server processes. |
| **`list_jobs`** | Lists all background processes previously started by the agent, showing process IDs and runtime states. |
| **`stop_job`** | Terminates a specific background job using its process ID. |

## Environment Configuration

The agent is configured using environment variables loaded via `dotenv`. The following variables dictate the runtime behavior:

* `OPENAI_API_KEY`: Required to authenticate with the OpenAI model provider.


* `OPENAI_MODEL`: Specifies the target language model to use for reasoning and generation.


* `HITL_ENABLED`: Toggle human-in-the-loop authorization; defaults to "true".


* `WORK_DIR`: Overrides the default workspace directory (`PROJECT_ROOT/workspace`).


* `MAX_MODEL_RUNS_PER_RUN`: Limits the number of sequential model calls per turn; defaults to 10.


* `MAX_READ_BYTES`: Limits the maximum file read size; defaults to 1,000,000 bytes.



## Security Guardrails

The agent utilizes a strictly enforced `ProtectionMiddleware` and sanitized shell commands to prevent destructive actions.

* **Path Restrictions:** Hard-blocks any access or modifications to sensitive files and directories, including `.env`, `.pem`, `.key`, `.git`, and `*.log`.


* **Payload Inspection:** Disallows file edits or writes that attempt to inject malicious patterns such as `subprocess`, `exec()`, `__import__()`, or `os.system()`.


* **Command Sanitization:** Intercepts and blocks dangerous shell commands including drive formatting (`mkfs`, `diskpart`), permission modifiers (`chmod 777`, `takeown.exe`), unverified network executions (`curl | sh`), and system reboots (`shutdown`, `reboot`).


* **Interpreter Rewriting:** Automatically rewrites Python and Pip commands (`python`, `flask`, `pip`) to use the project's virtual environment executable to avoid host environment pollution.


* **Size Limits:** Automatically intercepts and blocks attempts to read any file larger than 10MB to prevent context overflow.



## Usage

To start the agent, execute the main application via the CLI:

```bash
python src/main.py

```

Upon startup, the agent will load the `greeting.jinja` template and display the active provider, model, and working directory. Interact with the assistant using standard chat commands. If `HITL_ENABLED` is active, the terminal will pause and prompt `Allow [tool name]? y/n:` before any code writes, file edits, or shell commands are executed. Type `exit`, `quit`, or `q` at any time to terminate the session.