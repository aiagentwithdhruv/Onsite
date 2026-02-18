"""LLM configuration: API keys and model selection from Admin UI (app_config) or env. Builds client from selected model id."""

import time
import logging
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from app.core.llm_config import get_llm_api_key, get_llm_model_id
from app.core.llm_models import get_model_by_id
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MOONSHOT_BASE = "https://api.moonshot.ai/v1"


def _build_llm_from_model_id(model_id: str):
    """Build LangChain chat model from model id (primary/fast/fallback). Returns None if key missing."""
    info = get_model_by_id(model_id)
    if not info:
        return None
    provider = info["provider"]
    key = get_llm_api_key(provider)
    if not key:
        return None
    common = {"temperature": 0, "max_tokens": 4096}
    if provider == "anthropic":
        return ChatAnthropic(model=model_id, api_key=key, **common)
    if provider == "openai":
        return ChatOpenAI(model=model_id, api_key=key, **common)
    if provider == "openrouter":
        router_id = info.get("router_id") or model_id.replace("or:", "", 1)
        return ChatOpenAI(base_url=OPENROUTER_BASE, model=router_id, api_key=key, **common)
    if provider == "moonshot":
        return ChatOpenAI(base_url=MOONSHOT_BASE, model=model_id, api_key=key, **common)
    return None


def _build_sonnet():
    return _build_llm_from_model_id(get_llm_model_id("primary"))


def _build_haiku():
    return _build_llm_from_model_id(get_llm_model_id("fast"))


def _build_openai_fallback():
    return _build_llm_from_model_id(get_llm_model_id("fallback"))

# Model pricing (per 1M tokens)
PRICING = {
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
    "gpt-4o": {"input": 2.50, "output": 10.0},
}


def get_llm(task_type: str):
    """Returns appropriate LLM based on task complexity. Uses selected primary/fast model from Settings."""
    cheap_tasks = {"scoring", "ranking", "anomaly_detection", "assignment"}
    model_which = "fast" if task_type in cheap_tasks else "primary"
    llm = _build_llm_from_model_id(get_llm_model_id(model_which))
    if llm is None:
        fallback = _build_openai_fallback()
        if fallback is not None:
            return fallback
        raise ValueError(
            "No LLM configured. Set API key for the selected model's provider in Admin → Settings (LLM Providers), "
            "or set a fallback model whose provider has a key."
        )
    return llm


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD."""
    prices = PRICING.get(model, {"input": 3.0, "output": 15.0})
    return (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000


async def call_llm_with_fallback(llm, messages, fallback=None):
    """Try primary LLM, fall back to GPT-4o on failure."""
    if fallback is None:
        fallback = _build_openai_fallback()
    if fallback is None:
        log.warning("OpenAI API key not set; no fallback available.")

    try:
        response = await llm.ainvoke(messages)
        return response, llm.model
    except Exception as e:
        model_name = getattr(llm, "model", str(llm))
        log.warning("Primary LLM failed (%s): %s. Trying fallback.", model_name, e)
        if fallback is None:
            raise
        try:
            response = await fallback.ainvoke(messages)
            return response, getattr(fallback, "model_name", getattr(fallback, "model", "gpt-4o"))
        except Exception as e2:
            log.error("Fallback also failed: %s", e2)
            raise


async def tracked_llm_call(
    task_type: str,
    messages,
    lead_id: str | None = None,
    user_id: str | None = None,
):
    """Call LLM with fallback and log usage to ai_usage_log."""
    llm = get_llm(task_type)
    start = time.time()

    try:
        response, model_used = await call_llm_with_fallback(llm, messages)
        duration = int((time.time() - start) * 1000)

        input_tokens = response.usage_metadata.get("input_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0
        output_tokens = response.usage_metadata.get("output_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0
        cost = calculate_cost(model_used, input_tokens, output_tokens)

        # Log to DB
        db = get_supabase_admin()
        db.table("ai_usage_log").insert({
            "agent_type": task_type,
            "model": model_used,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "lead_id": lead_id,
            "triggered_by": user_id,
            "duration_ms": duration,
            "success": True,
        }).execute()

        return response

    except Exception as e:
        duration = int((time.time() - start) * 1000)
        db = get_supabase_admin()
        db.table("ai_usage_log").insert({
            "agent_type": task_type,
            "model": "failed",
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0,
            "duration_ms": duration,
            "success": False,
            "error_message": str(e)[:500],
        }).execute()
        raise
