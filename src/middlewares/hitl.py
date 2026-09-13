from langchain.agents.middleware import HumanInTheLoopMiddleware

def build_hitl_middleware () -> HumanInTheLoopMiddleware:
    """
        Middleware for Human in the Loop ability
    """
    return HumanInTheLoopMiddleware (
        interrupt_on={
            "read_file": False,
            "list_files": False,
            "list_jobs": False,
            "stop_job": False,
            "run_command": {
                "allowed_decisions": ["approve", "edit", "reject"],
                "description": "Run a bash command in the current working directory (host machine not a sandbox)"
            },
            "write_file": {
                "allowed_decisions": ["approve", "edit", "reject"],
                "description": "Write or overwrite a file on disk"
            },
            "edit_file": {
                "allowed_decisions": ["approve", "edit", "reject"],
                "description": "Edit files on disk"
            },
        },
        description_prefix="Coding agent needs your approval to move ahead"
    )