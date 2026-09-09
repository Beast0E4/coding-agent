from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy

from config.config import MAX_MODEL_RUNS_PER_RUN, hitl_enabled, AGENT_NAME
from middlewares import build_audit_middleware, build_protection_middleware, build_hitl_middleware
from models import build_chat_model
from tools import ALL_TOOLS
from prompts import build_system_prompt
from schema import TurnSummary

def build_middleware (
    *,
    enable_hitl: bool
) -> list:
    """
    Harness layers, outermost first
    
    1. model-call cap
    2. Audit log
    3. Payload guardrail
    4. HITL on write / edit / run
    """
    
    layers : list = [
        ModelCallLimitMiddleware (
            run_limit=MAX_MODEL_RUNS_PER_RUN,
            exit_behavior="exit"
        ),
        build_audit_middleware (),
        build_protection_middleware ()
    ]
    
    if enable_hitl:
        layers.append (build_hitl_middleware ())
    
    return layers

def build_agent (
    *,
    enable_hitl: bool | None = None,
    extra_guidance: str = ""
):
    model, _provider = build_chat_model ()
    use_hitl = hitl_enabled () if enable_hitl is None else enable_hitl
    
    return create_agent (
        model=model,
        tools=ALL_TOOLS,
        system_prompt=build_system_prompt (),
        extra_guidance="",
        middleware=build_middleware (enable_hitl=use_hitl),
        response_format=ProviderStrategy (TurnSummary),
        name=AGENT_NAME
    )