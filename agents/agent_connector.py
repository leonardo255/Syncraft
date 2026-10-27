from __future__ import annotations

import traceback
import uuid
import time
from typing import Dict, List, Tuple

from agents.models import ModelUnavailable, get_model
from langchain.messages import AIMessage, HumanMessage

from agents.syncraft_agent import SyncraftAgent

from app.state.graph_state import reset_graph_state, load_graph
from app.state.product_state import reset_products, load_products


# Simple in-memory session store: session_id -> list of BaseMessage
_session_store: Dict[str, List] = {}
_model = None
_agent: SyncraftAgent | None = None


def _get_model():
    global _model
    if _model is None:
        _model = get_model()  # raises ModelUnavailable if not configured
    return _model


def _status_code(exc: BaseException) -> int | None:
    """HTTP status of a provider error, looking through wrapped exceptions."""
    seen = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        code = getattr(exc, "status_code", None)
        if code is None:
            code = getattr(getattr(exc, "response", None), "status_code", None)
        if isinstance(code, int):
            return code
        exc = exc.__cause__ or exc.__context__
    return None


def _friendly_error(exc: BaseException) -> str:
    """A short message for the chat; details go to the server log."""
    if isinstance(exc, ModelUnavailable):
        return f"⚠️ {exc} Please contact the Syncraft team."
    code = _status_code(exc)
    name = type(exc).__name__
    if code in (401, 403) or "Authentication" in name or "PermissionDenied" in name:
        return "⚠️ The demo is not set up to answer right now. Please contact the Syncraft team."
    if code == 429 or "RateLimit" in name:
        return "⚠️ The demo is busy right now. Please try again in a minute."
    if "Timeout" in name or "Connection" in name:
        return "⚠️ I couldn't answer just now. Please try again in a moment."
    return "⚠️ Something went wrong while answering. Please try again."


def _get_agent() -> SyncraftAgent:
    global _agent
    if _agent is None:
        _agent = SyncraftAgent(model=_get_model())
    return _agent


def _get_history(session_id: str) -> List:
    if session_id not in _session_store:
        _session_store[session_id] = []
    return _session_store[session_id]


def reset_session(session_id: str) -> None:
    """
    Clear stored history and agent state for a session.
    In Streamlit Cloud, ensures files are properly reset and reloaded.
    """
    global _agent

    _session_store[session_id] = []
    reset_products()
    reset_graph_state()
    
    # Small delay to ensure file writes are flushed to disk on Streamlit Cloud
    time.sleep(0.1)
    
    # Force reload to verify empty state was written
    _ = load_graph()
    _ = load_products()

    # The agent is rebuilt lazily on the next message, so resetting also
    # works when no model is configured.
    _agent = None



def get_display_history(session_id: str) -> List[dict]:
    """Return UI-friendly history for a session."""
    history = _get_history(session_id)
    return [
        {"role": "assistant" if isinstance(m, AIMessage) else "user", "content": m.content}
        for m in history
    ]


def new_session_id() -> str:
    return str(uuid.uuid4())


def send_message(session_id: str, user_message: str) -> Tuple[str, List[dict]]:
    """
    Send a user message through the agent.
    Returns (assistant_reply, display_history) where display_history is a list of dicts
    with role/content for UI rendering.
    """
    history = _get_history(session_id)

    try:
        agent = _get_agent()
        # Directly send the raw user string to the agent
        response_text = agent.go_to_work(user_instructions=user_message)
    except Exception as exc:
        # Never crash the page: log the details, answer with a short message.
        print(f"[syncraft] request failed: {exc!r}", flush=True)
        traceback.print_exc()
        response_text = _friendly_error(exc)
    assistant_msg = AIMessage(content=response_text)

    # Persist turn
    history.extend([HumanMessage(content=user_message), assistant_msg])

    # Prepare display-friendly history
    display_history = [
        {"role": "assistant" if isinstance(m, AIMessage) else "user", "content": m.content}
        for m in history
    ]
    return assistant_msg.content, display_history

