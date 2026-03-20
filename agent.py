# agent.py

from dotenv import load_dotenv
import os
import re
from openai import OpenAI

from tools import (
    get_order_status,
    check_return_eligibility,
    create_return_request
)
from policies import lookup_policy
from prompts import SYSTEM_PROMPT

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Check your .env file.")

client = OpenAI(api_key=api_key)


def generate_response(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""
You are responding to a customer support message.

Follow the instructions EXACTLY.
Do not default to a generic greeting.
Do not introduce yourself unless the customer greets you first.

{prompt}
"""
            }
        ],
        temperature=0.1
    )
    return response.choices[0].message.content


def ai_response(instruction: str):
    prompt = f"""
Customer interaction context:
{instruction}

Respond directly to the customer.
Do not greet or introduce yourself unless explicitly asked.
Be concise, helpful, and professional.
"""
    return generate_response(prompt)


def detect_intent(message: str):
    msg = message.lower()

    if any(x in msg for x in ["return", "refund"]):
        return "return_request"

    if any(x in msg for x in [
        "order status",
        "track order",
        "track",
        "status",
        "where is my order",
        "where is order",
        "where is my package",
        "where is my delivery",
    ]):
        return "order_status"

    if "order" in msg and any(char.isdigit() for char in msg):
        return "order_status"

    if any(x in msg for x in ["shipping", "policy", "password"]):
        return "faq"

    return "unknown"


def detect_closing(message: str):
    msg = message.lower().strip()
    closing_phrases = [
        "thanks",
        "thank you",
        "thx",
        "ok",
        "okay",
        "no",
        "nope",
        "all good",
        "all set",
        "that is all",
        "that's all",
        "done"
    ]
    return msg in closing_phrases


def extract_order_id(message: str):
    match = re.search(r"\b\d{3,6}\b", message)
    return match.group(0) if match else None


def handle_message(user_message: str, state: dict) -> str:
    user_message = user_message.strip()

    # ---- Closing / conversation end ----
    if detect_closing(user_message) and state.get("current_intent") is None:
        return generate_response("""
The customer is signaling that they are done, for example by saying thanks or no.

Respond naturally and briefly to close the conversation.
Do not repeat your capabilities.
Do not ask another question.
Be polite and professional.
""")

    # ---- Order status flow: waiting for order id ----
    if state.get("current_intent") == "order_status" and not state.get("order_id"):
        order_id = extract_order_id(user_message) or user_message
        state["order_id"] = order_id

        result = get_order_status(order_id)

        if not result["success"]:
            state["order_id"] = None
            return ai_response(
                "The customer is trying to check an order status, but the order was not found. "
                "Ask them to double-check the order ID and try again."
            )

        prompt = f"""
The customer asked about their order status.

Respond using ONLY the information below.

Order ID: {order_id}
Status: {result['status']}
Estimated delivery: {result['estimated_delivery']}

Provide a direct answer to the customer.
Do not greet or introduce yourself.
"""
        state["current_intent"] = None
        state["order_id"] = None
        return generate_response(prompt)

    # ---- Return flow: step 1 (collect order_id) ----
    if state.get("current_intent") == "return_request" and not state.get("order_id"):
        order_id = extract_order_id(user_message) or user_message
        state["order_id"] = order_id

        result = check_return_eligibility(order_id)

        if not result["success"]:
            state["order_id"] = None
            return ai_response(
                "The customer wants to start a return, but the order was not found. "
                "Ask them to check the order ID."
            )

        if not result["eligible"]:
            state["current_intent"] = None
            state["order_id"] = None
            return generate_response(f"""
The customer wants to start a return, but the order is not eligible.

Respond using ONLY the information below.

Reason: {result['reason']}

Explain this clearly and empathetically.
Do not greet or introduce yourself.
""")

        state["eligible_items"] = result["items"]
        return generate_response(f"""
The customer is eligible for a return.

Respond using ONLY the information below.

Eligible items: {result['items']}

Ask the customer which item they would like to return.
Do not greet or introduce yourself.
""")

    # ---- Return flow: step 2 (collect item) ----
    if state.get("current_intent") == "return_request" and not state.get("selected_item"):
        item = user_message
        eligible_items = state.get("eligible_items") or []

        if item not in eligible_items:
            return generate_response(f"""
The customer is trying to select an item to return, but their selection does not exactly match the eligible items.

Respond using ONLY the information below.

Eligible items: {eligible_items}
Customer selection: {item}

Ask them to choose one of the eligible items.
Do not greet or introduce yourself.
""")

        state["selected_item"] = item
        return ai_response(
            "The customer selected the item they want to return. Ask them for the reason for the return."
        )

    # ---- Return flow: step 3 (collect reason + execute) ----
    if state.get("current_intent") == "return_request" and not state.get("return_reason"):
        reason = user_message
        state["return_reason"] = reason

        result = create_return_request(
            state["order_id"],
            state["selected_item"],
            state["return_reason"]
        )

        state["current_intent"] = None
        state["order_id"] = None
        state["selected_item"] = None
        state["return_reason"] = None
        state["eligible_items"] = None

        if not result["success"]:
            return ai_response(
                "The system was unable to create the return request. "
                "Tell the customer something went wrong and ask them to try again."
            )

        prompt = f"""
The customer successfully created a return request.

Respond using ONLY the information below.

Return ID: {result['return_id']}
Item: {result['item']}
Reason: {result['reason']}

Confirm the return clearly.
End with a natural, short closing sentence.
Do not list capabilities.
Do not ask follow-up questions.
Do not greet or introduce yourself.
"""
        return generate_response(prompt)

    # ---- New request ----
    intent = detect_intent(user_message)
    state["current_intent"] = intent

    if intent == "order_status":
        order_id = extract_order_id(user_message)

        if order_id:
            state["order_id"] = order_id

            result = get_order_status(order_id)

            if not result["success"]:
                state["current_intent"] = None
                state["order_id"] = None
                return ai_response(
                    "The customer is trying to check an order status, but the order was not found. "
                    "Ask them to verify the order ID."
                )

            prompt = f"""
The customer asked about their order status.

Respond using ONLY the information below.

Order ID: {order_id}
Status: {result['status']}
Estimated delivery: {result['estimated_delivery']}

Provide a direct answer to the customer.
Do not greet or introduce yourself.
"""
            state["current_intent"] = None
            state["order_id"] = None
            return generate_response(prompt)

        state["order_id"] = None
        return ai_response(
            "The customer wants to check their order status but did not provide an order ID. "
            "Ask them to share their order ID."
        )

    if intent == "return_request":
        order_id = extract_order_id(user_message)
        state["selected_item"] = None
        state["return_reason"] = None
        state["eligible_items"] = None

        if order_id:
            state["order_id"] = order_id

            result = check_return_eligibility(order_id)

            if not result["success"]:
                state["current_intent"] = None
                state["order_id"] = None
                return ai_response(
                    "The customer wants to start a return, but the order was not found. "
                    "Ask them to verify the order ID."
                )

            if not result["eligible"]:
                state["current_intent"] = None
                state["order_id"] = None
                return generate_response(f"""
The customer wants to start a return, but the order is not eligible.

Respond using ONLY the information below.

Reason: {result['reason']}

Explain this clearly and empathetically.
Do not greet or introduce yourself.
""")

            state["eligible_items"] = result["items"]
            return generate_response(f"""
The customer is eligible for a return.

Respond using ONLY the information below.

Eligible items: {result['items']}

Ask the customer which item they would like to return.
Do not greet or introduce yourself.
""")

        state["order_id"] = None
        return ai_response(
            "The customer wants to start a return but did not provide an order ID. "
            "Ask them to share their order ID."
        )

    if intent == "faq":
        if "shipping" in user_message.lower():
            policy = lookup_policy("shipping")
            return generate_response(f"""
The customer is asking about shipping.

Respond using ONLY the information below.

Policy: {policy}

Answer the customer directly.
Do not greet or introduce yourself.
""")

        if "return" in user_message.lower():
            policy = lookup_policy("returns")
            return generate_response(f"""
The customer is asking about the return policy.

Respond using ONLY the information below.

Policy: {policy}

Answer the customer directly.
Do not greet or introduce yourself.
""")

        if "password" in user_message.lower():
            policy = lookup_policy("password_reset")
            return generate_response(f"""
The customer is asking how to reset their password.

Respond using ONLY the information below.

Policy: {policy}

Answer the customer directly.
Do not greet or introduce yourself.
""")

        return generate_response(f"""
The user said: "{user_message}"

If this is a Bookly support question but unclear, ask a simple clarifying question.
If it is outside supported FAQ topics, say you can help with shipping, returns, or password reset.
Do not list all capabilities unless necessary.
Be concise and natural.
Do not greet or introduce yourself.
""")

    return generate_response(f"""
The user said: "{user_message}"

If this message is unclear, ask a simple clarifying question.
If it is outside the currently supported support flows, explain briefly that you can help with order status, returns, shipping questions, and password reset guidance.
Do not list capabilities unless necessary.
Be concise and natural.
Do not greet or introduce yourself.
""")