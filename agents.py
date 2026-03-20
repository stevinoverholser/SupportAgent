# agent.py

from tools import (
    get_order_status,
    check_return_eligibility,
    create_return_request
)

from policies import lookup_policy


# Intent Detection (simple + reliable)

def detect_intent(message: str):
    msg = message.lower()

    if any(x in msg for x in ["return", "refund"]):
        return "return_request"

    if any(x in msg for x in ["track order", "order status", "where is my order", "track", "status"]):
        return "order_status"

    if any(x in msg for x in ["shipping", "policy", "password"]):
        return "faq"

    return "unknown"



# Main Handler

def handle_message(user_message: str, state: dict) -> str:
    """
    Core agent logic.
    state = streamlit session_state
    """

    user_message = user_message.strip()

    # -------------------------
    # STEP 1: Handle ongoing flows first
    # -------------------------

    # ---- Order status flow ----
    if state.get("current_intent") == "order_status" and not state.get("order_id"):
        order_id = user_message
        state["order_id"] = order_id

        result = get_order_status(order_id)

    if not result["success"]:
        state["order_id"] = None
        return "I couldn’t find that order. Please check the order ID and try again."

        prompt = f"""
    Generate a helpful customer support response using ONLY this information:

    Order ID: {order_id}
    Status: {result['status']}
    Estimated delivery: {result['estimated_delivery']}

    Be concise and friendly. Do not add any information not provided. test
    """

    return generate_response(prompt)

    # ---- Return flow: step 1 (collect order_id) ----
    if state.get("current_intent") == "return_request" and not state.get("order_id"):
        order_id = user_message
        state["order_id"] = order_id

        result = check_return_eligibility(order_id)

        if not result["success"]:
            state["order_id"] = None
            return "I couldn’t find that order. Please check the order ID."

        if not result["eligible"]:
            state["current_intent"] = None
            state["order_id"] = None
            return f"This order is not eligible for return. {result['reason']}"

        state["eligible_items"] = result["items"]
        return f"This order is eligible for return. Which item would you like to return? {result['items']}"

    # ---- Return flow: step 2 (collect item) ----
    if state.get("current_intent") == "return_request" and not state.get("selected_item"):
        item = user_message
        state["selected_item"] = item
        return "Got it. What is the reason for the return?"

    # ---- Return flow: step 3 (collect reason + execute) ----
    if state.get("current_intent") == "return_request" and not state.get("return_reason"):
        reason = user_message
        state["return_reason"] = reason

        result = create_return_request(
            state["order_id"],
            state["selected_item"],
            state["return_reason"]
        )

        # reset state after completion
        state["current_intent"] = None
        state["order_id"] = None
        state["selected_item"] = None
        state["return_reason"] = None

        if not result["success"]:
            return "Something went wrong creating your return. Please try again."

        return f"Your return has been created successfully. Return ID: {result['return_id']}"

  
    # STEP 2: New request (no active flow)
  

    intent = detect_intent(user_message)
    state["current_intent"] = intent

    # ---- Order status ----
    if intent == "order_status":
        state["order_id"] = None
        return "I can help with that. What is your order ID?"

    # ---- Return request ----
    if intent == "return_request":
        state["order_id"] = None
        state["selected_item"] = None
        state["return_reason"] = None
        return "Sure, I can help with a return. What is your order ID?"

    # ---- FAQ ----
    if intent == "faq":
        if "shipping" in user_message.lower():
            return lookup_policy("shipping")

        if "return" in user_message.lower():
            return lookup_policy("returns")

        if "password" in user_message.lower():
            return lookup_policy("password_reset")

        return "I can help with shipping, returns, or password reset. What would you like to know?"

    # ---- Unknown / Clarification ----
    return "I can help with order status, returns, or general questions. What would you like help with?"