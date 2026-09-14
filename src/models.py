import os
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv ()

@dataclass (frozen = True)
class Provider:
    name: str
    env_var: str
    is_free: bool
    base_url: str | None
    model: str
    
PROVIDERS = [
    Provider (
        "OpenAI",
        "OPENAI_API_KEY",
        False,
        None, 
        os.getenv ("OPENAI_MODEL")
    )
]

def select_provider () -> Provider:
    for provider in PROVIDERS:
        if os.getenv (provider.env_var):
            return provider
        
    raise RuntimeError ("No providers present")

def build_chat_model () -> tuple[ChatOpenAI, Provider]:
    provider = select_provider ()
    kwargs: dict = {
        "model": provider.model,
        "api_key": os.getenv (provider.env_var)
    }
    
    if provider.base_url is not None:
        kwargs["base_url"] = provider.base_url
        
    return ChatOpenAI (**kwargs), provider