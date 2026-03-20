POLICIES = {
    "shipping": "Standard shipping takes 3 to 5 business days. Expedited shipping takes 1 to 2 business days.",
    "returns": "Books may be returned within 30 days of delivery if they are in original condition.",
    "password_reset": "To reset your password, click 'Forgot Password' on the sign-in page and follow the email instructions.",
}

def lookup_policy(topic: str):
    return POLICIES.get(topic)