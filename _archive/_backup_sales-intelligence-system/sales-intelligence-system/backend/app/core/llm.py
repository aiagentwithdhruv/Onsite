"""LLM configuration with automatic fallback: Claude → GPT-4o."""

import time
import logging
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from app.core.config import get_settings
from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)

settings = get_settings()

# Primary models
llm_sonnet = ChatAnthropic(
    model="claude-sonnet-4-5-20250929",
    api_key=settings.anthropic_api_key,
    temperature=0,
    max_tokens=4096,
)

llm_haiku = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    api_key=settings.anthropic_api_key,
    temperature=0,
    max_tokens=4096,
)

# Fallback
llm_fallback = ChatOpenAI(
    model="gpt-4o",
    api_key=settings.openai_api_key,
    temperature=0,
    max_tokens=4096,
)

# Model pricing (per 1M tokens)
PRICING = {
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
    "gpt-4o": {"input": 2.50, "output": 10.0},
}


def get_llm(task_type: str):
    """Returns appropriate LLM based on task complexity."""
    cheap_tasks = {"scoring", "ranking", "anomaly_detection", "assignment"}
    if task_type in cheap_tasks:
        return llm_haiku
    return llm_sonnet


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD."""
    prices = PRICING.get(model, {"input": 3.0, "output": 15.0})
    return (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000


async def call_llm_with_fallback(llm, messages, fallback=None):
    """Try primary LLM, fall back to GPT-4o on failure."""
    if fallback is None:
        fallback = llm_fallback

    try:
        response = await llm.ainvoke(messages)
        return response, llm.model
    except Exception as e:
        log.warning(f"Primary LLM failed ({llm.model}): {e}. Falling back to GPT-4o.")
        try:
            response = await fallback.ainvoke(messages)
            return response, fallback.model_name
        except Exception as e2:
            log.error(f"Fallback also failed: {e2}")
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
