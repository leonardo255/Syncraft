"""The chat model the agents use.

Choose it with LLM_MODEL (any "provider:model" string init_chat_model accepts),
default anthropic:claude-haiku-4-5. Only the chosen provider's API key is needed,
e.g. ANTHROPIC_API_KEY for anthropic:..., OPENAI_API_KEY for openai:...,
MISTRAL_API_KEY for mistralai:....

The model is created on first use, not at import, so a missing or broken
configuration never stops the app from starting - get_model() raises
ModelUnavailable with a generic message for the user; the details go to the log.
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

DEFAULT_MODEL = "anthropic:claude-haiku-4-5"
MODEL_NAME = os.getenv("LLM_MODEL", DEFAULT_MODEL)

# Environment variable holding the API key, per provider prefix of LLM_MODEL.
API_KEY_VARS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "mistralai": "MISTRAL_API_KEY",
}


class ModelUnavailable(RuntimeError):
    """The model can't be used; str(exc) is safe to show to the user."""


_model = None


def api_key_var() -> str | None:
    provider = MODEL_NAME.split(":", 1)[0] if ":" in MODEL_NAME else None
    return API_KEY_VARS.get(provider or "")


def get_model():
    """Return the configured chat model, or raise ModelUnavailable."""
    global _model
    if _model is not None:
        return _model

    key_var = api_key_var()
    if key_var and not os.getenv(key_var, "").strip():
        # Details for the server log only; the user sees a generic message.
        print(f"[syncraft] {key_var} is not set - cannot use {MODEL_NAME!r}", flush=True)
        raise ModelUnavailable("The demo is not set up to answer right now.")
    try:
        _model = init_chat_model(MODEL_NAME, temperature=0.5, timeout=30, max_tokens=5000)
    except Exception as exc:  # unknown provider, missing package, bad settings
        print(f"[syncraft] could not create model {MODEL_NAME!r}: {exc!r}", flush=True)
        raise ModelUnavailable("The demo is not set up to answer right now.") from exc
    return _model
