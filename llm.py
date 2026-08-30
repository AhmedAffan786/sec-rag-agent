"""
Shared local LLM client — every node that needs to think (Manager,
Drafter, Comparator) gets its model from here, so we configure Ollama
in exactly one place.
"""

from langchain_ollama import ChatOllama

import config

_llm = None


def get_llm(temperature: float = 0.0) -> ChatOllama:
    """Returns a shared ChatOllama client. temperature=0.0 by default
    for deterministic routing/classification decisions; pass a higher
    value (e.g. 0.7) when calling this for creative drafting in Stage 4."""
    global _llm
    if _llm is None:
        _llm = ChatOllama(
            model=config.OLLAMA_MODEL_NAME,
            base_url=config.OLLAMA_BASE_URL,
            temperature=temperature,
        )
    return _llm