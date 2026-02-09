import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))


import streamlit as st
import numpy as np
import time
from app.state.graph_state import load_graph
from app.state.product_state import load_products
from ui.plotly_graph import build_graph_figure
    
from agents.agent_connector import (
    get_display_history,
    new_session_id,
    reset_session,
    send_message,
)


def main():
    # Page config
    st.set_page_config(page_title="Syncraft Chat", page_icon="💬", layout="wide")
    assets_dir = Path(__file__).parent / "assets" / "images"
    bot_avatar = assets_dir / "agent.png"  # placeholder; replace with your bot image
    user_avatar = None  # leave None to use a speech bubble by default

    def resolve_avatar(path: Path | None, fallback: str) -> str:
        # Return a valid avatar target; Streamlit accepts emoji, URL, or local path.
        return str(path) if path and path.exists() else fallback

    # Session bootstrap
    if "session_id" not in st.session_state:
        st.session_state.session_id = new_session_id()
    if "messages" not in st.session_state:
        st.session_state.messages = get_display_history(st.session_state.session_id)
        if not st.session_state.messages:
            st.session_state.messages = [
                {"role": "assistant", "content": "Hi! Ask me to setup a production simulation."}
            ]
    # Mirror global graph
    if "graph" not in st.session_state:
        st.session_state.graph = load_graph()

    if "products" not in st.session_state:
        st.session_state.products = load_products()

    # Title
    st.title("Syncraft")

    # Render chat history
    st.caption("Your agentic production simulation assistant.")
    for msg in st.session_state.messages:
        avatar = resolve_avatar(
            bot_avatar if msg["role"] == "assistant" else user_avatar,
            "🤖" if msg["role"] == "assistant" else "💬",
        )
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    

    # Input box at the bottom
    if raw_input := st.chat_input("Type your message"):
        # st.chat_input can return str or a dict-like (when files/audio are enabled).
        if isinstance(raw_input, str):
            user_input = raw_input
        elif isinstance(raw_input, dict):
            user_input = raw_input.get("text", "")
        else:
            user_input = getattr(raw_input, "text", "") or ""

        if not user_input:
            st.warning("Please enter a message.")
            st.stop()

        with st.chat_message("user", avatar=resolve_avatar(user_avatar, "💬")):
            st.markdown(user_input)

        response, updated_history = send_message(
            session_id=st.session_state.session_id, user_message=user_input
        )

        with st.chat_message("assistant", avatar=resolve_avatar(bot_avatar, "🤖")):
            st.markdown(response)


        # Update UI adter agent calls
        st.session_state.messages = updated_history
        st.session_state.graph = load_graph()
        st.session_state.products = load_products()
        print(st.session_state.graph)


    # Sidebar for future controls
    with st.sidebar:
        logo_path = assets_dir / "sdu_logo.png"
        if logo_path.exists():
            st.image(str(logo_path))
        st.subheader("Session Controls")
        if st.button("Reset chat"):
            reset_session(st.session_state.session_id)
            st.session_state.session_id = new_session_id()
            st.session_state.messages = [
                {"role": "assistant", "content": "Hi! Ask me to setup a production simulation."}
            ]
            st.experimental_rerun()

        # Products overview
        st.subheader("Products")
        products = st.session_state.get("products", []) or []
        if not products:
            st.caption("No products configured yet.")
        else:
            for p in products:
                label = p.get("label", "Unnamed")
                color = p.get("color", "#888888")
                st.markdown(
                    f"<span style='font-size: 1.2em; color:{color};'>●</span> {label}",
                    unsafe_allow_html=True,
                )

    # Plotly graph
    st.divider()

    fig = build_graph_figure(
        graph=st.session_state.graph,
        products=st.session_state.products,
        n_steps=50,
    )

    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


if __name__ == "__main__":
    main()