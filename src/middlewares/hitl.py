from langchain.agents.middleware import HumanInTheLoopMiddleware

def build_hitl_middleware () -> HumanInTheLoopMiddleware:
    """
        Middleware for Human in the Loop ability
    """
    return HumanInTheLoopMiddleware (
        interrupt_on={
            "read_file": False,
            "list_files": False,
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