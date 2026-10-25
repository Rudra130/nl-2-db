"""LLM Client Factory and Prompt Utilities."""
from typing import Optional, Union
from backend.app.config import Settings, get_settings
from .nim_client import NvidiaNIMClient
from .mock_client import MockLLMClient

LLMClientType = Union[NvidiaNIMClient, MockLLMClient]


def get_llm_client(settings: Optional[Settings] = None) -> LLMClientType:
    """Return configured LLM client: NvidiaNIMClient if API key present and USE_MOCK_LLM is False, else MockLLMClient."""
    s = settings or get_settings()
    if s.USE_MOCK_LLM or not s.NVIDIA_NIM_API_KEY.strip():
        return MockLLMClient(settings=s)
    return NvidiaNIMClient(settings=s)


__all__ = ["NvidiaNIMClient", "MockLLMClient", "get_llm_client", "LLMClientType"]
