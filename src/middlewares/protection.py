import json
import re

from typing import Any

from collections.abc import Callable

from langchain.agents.middleware import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command

from tools.paths import is_blocked, resolve_work_path

FILE_TOOLS = {"read_file", "write_file", "list_files", "edit_file"}

BLOCKED_EDIT_PATTERNS = (
    r"\bos\.system\s*\(",
    r"\bsubprocess\b",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"__import__\s*\(",
)

def _tool_message (request: ToolCallRequest, reason: str) -> ToolMessage:
    return ToolMessage (
        content = reason,
        tool_call_id = request.tool_call["id"],
        name = request.tool_call["name"],
        
    )

def _deny_reason (tool_name: str, arguments: dict[str, Any]) -> str | None:
    """
    Returns a denial reason or none for a tool called being referred
    """
    if tool_name == "run_command":
        return None
    
    if tool_name not in FILE_TOOLS:
        return None
    
    path = arguments.get ("path", ".")
    
    if is_blocked (str (path)):
        return (
            f"Blocked by middleware : Access to protected path {path} is not allowed"
        )
        
    if tool_name == "read_file":
        try:
            file_path = resolve_work_path (str (path))
        except ValueError as e:
            return f"Blocked by middleware : {e}"
        
        if file_path.is_file () and file_path.stat ().st_size > 1024 * 1024 * 10: # 10 MB
            return (
                f"Blocked by middleware : File {file_path} is too large to read"
            )
            
    payload = ""
    if tool_name == "edit_file":
        payload = str (arguments.get ("new_str", ""))
    elif tool_name == "write_file":
        payload = str (arguments.get ("content", ""))
        
    if payload:
        for pattern in BLOCKED_EDIT_PATTERNS:
            if re.search (pattern, payload):
                return (
                    f"Blocked by middleware : suspicious payload contains {pattern!r}"
                )
    
    return None

class ProtectionMiddleware (AgentMiddleware):
    """ Shortcircuit tool calls that target secrets or dangerous payloads """
    
    def wrap_tool_call (
        self, 
        request : ToolCallRequest, 
        handler: Callable[[ToolCallRequest], ToolMessage | Command]
    ) -> ToolMessage | Command:
        name = request.tool_call.get ('name', "")
        arguments = request.tool_call.get ('args', {})
        
        reason = _deny_reason (name, arguments)
        
        if reason is not None:
            return _tool_message (request, reason)
        
        return handler(request)
    
def build_protection_middleware() -> ProtectionMiddleware:
    """Factory function to instantiate the audit middleware."""
    return ProtectionMiddleware ()