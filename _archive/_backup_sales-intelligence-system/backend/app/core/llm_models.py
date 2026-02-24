"""
Available LLM models for OpenAI, Anthropic, OpenRouter, and Moonshot.
Admin can select primary / fast / fallback from Settings.
"""

from typing import TypedDict


class LLMModel(TypedDict):
    id: str
    label: str
    description: str
    provider: str
    router_id: str | None  # OpenRouter model id (e.g. google/gemini-2.5-pro)


# Top models per provider (aligned with angelina-vercel-clean and common usage)
TEXT_MODELS: list[LLMModel] = [
    # OpenAI (direct)
    {"id": "gpt-4o", "label": "GPT-4o", "description": "Multimodal, strong all-round", "provider": "openai", "router_id": None},
    {"id": "gpt-4o-mini", "label": "GPT-4o Mini", "description": "Fast + cheap", "provider": "openai", "router_id": None},
    {"id": "gpt-4.1-mini", "label": "GPT-4.1 Mini", "description": "Fast + capable", "provider": "openai", "router_id": None},
    {"id": "gpt-4.1", "label": "GPT-4.1", "description": "Best for coding", "provider": "openai", "router_id": None},
    {"id": "o3-mini", "label": "o3-mini", "description": "Reasoning model", "provider": "openai", "router_id": None},
    # Anthropic (direct)
    {"id": "claude-sonnet-4-5-20250929", "label": "Claude Sonnet 4.5", "description": "Speed + intelligence", "provider": "anthropic", "router_id": None},
    {"id": "claude-haiku-4-5-20251001", "label": "Claude Haiku 4.5", "description": "Fastest Claude", "provider": "anthropic", "router_id": None},
    {"id": "claude-opus-4-6", "label": "Claude Opus 4.6", "description": "Most capable", "provider": "anthropic", "router_id": None},
    # OpenRouter (single API key, many models)
    {"id": "or:deepseek/deepseek-v3.2", "label": "DeepSeek V3.2", "description": "GPT-class, cost-effective", "provider": "openrouter", "router_id": "deepseek/deepseek-v3.2"},
    {"id": "or:deepseek/deepseek-r1", "label": "DeepSeek R1", "description": "Deep reasoning", "provider": "openrouter", "router_id": "deepseek/deepseek-r1"},
    {"id": "or:google/gemini-2.5-pro", "label": "Gemini 2.5 Pro (OR)", "description": "Via OpenRouter", "provider": "openrouter", "router_id": "google/gemini-2.5-pro"},
    {"id": "or:google/gemini-2.5-flash", "label": "Gemini 2.5 Flash (OR)", "description": "Fast + cheap via OR", "provider": "openrouter", "router_id": "google/gemini-2.5-flash"},
    {"id": "or:google/gemini-3-flash-preview", "label": "Gemini 3 Flash Preview", "description": "Latest Gemini, fast", "provider": "openrouter", "router_id": "google/gemini-3-flash-preview"},
    {"id": "or:moonshotai/kimi-k2.5", "label": "Kimi K2.5 (OR)", "description": "Visual coding SOTA", "provider": "openrouter", "router_id": "moonshotai/kimi-k2.5"},
    {"id": "or:moonshotai/kimi-k2-thinking", "label": "Kimi K2 Thinking (OR)", "description": "Deep reasoning", "provider": "openrouter", "router_id": "moonshotai/kimi-k2-thinking"},
    {"id": "or:openai/gpt-4.1-mini-2025-04-14", "label": "GPT-4.1 Mini (OR)", "description": "Via OpenRouter", "provider": "openrouter", "router_id": "openai/gpt-4.1-mini-2025-04-14"},
    {"id": "or:meta-llama/llama-4-scout-17b-16e-instruct", "label": "Llama 4 Scout (OR)", "description": "Meta open model", "provider": "openrouter", "router_id": "meta-llama/llama-4-scout-17b-16e-instruct"},
    # Moonshot / Kimi (direct)
    {"id": "moonshot-v1-128k", "label": "Moonshot V1 128K", "description": "128K context", "provider": "moonshot", "router_id": None},
    {"id": "kimi-k2.5", "label": "Kimi K2.5", "description": "Visual coding SOTA", "provider": "moonshot", "router_id": None},
    {"id": "kimi-k2-thinking", "label": "Kimi K2 Thinking", "description": "Deep reasoning", "provider": "moonshot", "router_id": None},
]

MODEL_IDS = [m["id"] for m in TEXT_MODELS]

DEFAULT_PRIMARY = "claude-sonnet-4-5-20250929"
DEFAULT_FAST = "claude-haiku-4-5-20251001"
DEFAULT_FALLBACK = "gpt-4o"


def get_model_by_id(model_id: str) -> LLMModel | None:
    for m in TEXT_MODELS:
        if m["id"] == model_id:
            return m
    return None


def get_provider_for_model(model_id: str) -> str:
    m = get_model_by_id(model_id)
    return m["provider"] if m else "anthropic"
