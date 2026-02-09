from __future__ import annotations

import uuid
from typing import Dict, List, Tuple

from agents.models import LLM_MODEL
from langchain.messages import AIMessage, HumanMessage

from agents.syncraft_agent import SyncraftAgent


# Simple in-memory session store: session_id -> list of BaseMessage
_session_store: Dict[str, List] = {}
_model = None
_agent: SyncraftAgent | None = None


def _get_model():
    global _model
    if _model is None:
        _model = LLM_MODEL
    return _model


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
    """Clear stored history for a session."""
    _session_store.pop(session_id, None)


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
    agent = _get_agent()
    history = _get_history(session_id)

    # Directly send the raw user string to the agent
    response_text = agent.go_to_work(user_instructions=user_message)
    assistant_msg = AIMessage(content=response_text)

    # Persist turn
    history.extend([HumanMessage(content=user_message), assistant_msg])

    # Prepare display-friendly history
    display_history = [
        {"role": "assistant" if isinstance(m, AIMessage) else "user", "content": m.content}
        for m in history
    ]
    return assistant_msg.content, display_history

