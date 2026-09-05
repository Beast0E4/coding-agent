import json

from typing import Any

from collections.abc import Callable

from datetime import datetime, UTC

from langchain.agents.middleware import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command

from config.config import get_work_directory

class AuditMiddleware(AgentMiddleware):
    """Append a JSON log after each tool call"""

    def wrap_tool_call (
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        result = handler (request)
        preview = ""
        if isinstance (result, ToolMessage):
            preview = str (result.content)[:200]
        
        self._write ({
            "timestamp": datetime.now (UTC).isoformat (),
            "tool": request.tool_call.get ('name'),
            "result_preview": preview,
            "arguments": request.tool_call.get ('args'),
        })
        
        return result
            
    def _write (
        self, 
        entry: dict[str, Any]
    ) -> None:
        log_path = get_work_directory () / "agent_audit.log"
        log_path.parent.mkdir (parents = True, exist_ok=True)
        with log_path.open ("a", encoding='utf-8') as f:
            f.write (json.dumps (entry) + "\n")
        
         


def build_audit_middleware() -> AuditMiddleware:
    """Factory function to instantiate the audit middleware."""
    return AuditMiddleware()