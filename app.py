# app.py

import streamlit as st
from agent import handle_message

st.set_page_config(page_title="Bookly Support Agent", page_icon="📚")

st.title("📚 Bookly Support Agent")
st.caption("Ask about order status, returns, shipping, or password reset.")


# Initialize session state

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_intent" not in st.session_state:
    st.session_state.current_intent = None

if "order_id" not in st.session_state:
    st.session_state.order_id = None

if "selected_item" not in st.session_state:
    st.session_state.selected_item = None

if "return_reason" not in st.session_state:
    st.session_state.return_reason = None

if "eligible_items" not in st.session_state:
    st.session_state.eligible_items = None

# Optional greeting on first load
if len(st.session_state.messages) == 0:
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hi, I’m the Bookly Support Agent. I can help with order status, returns, shipping questions, and password reset guidance."
    })


# Render chat history

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# Chat input

user_input = st.chat_input("Type your question here...")

if user_input:
    # Show user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.write(user_input)

    # Get assistant response
    response = handle_message(user_input, st.session_state)

    # Save and display assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

    with st.chat_message("assistant"):
        st.write(response)