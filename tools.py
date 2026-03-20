from datetime import datetime

ORDERS = {
    "0001": {
        "email": "stevin@example.com",
        "status": "Shipped",
        "estimated_delivery": "March 22, 2026",
        "items": ["The Great Gatsby"],
        "delivered_days_ago": None,
    },
    "0002": {
        "email": "kat@example.com",
        "status": "Delivered",
        "estimated_delivery": None,
        "items": ["Dune"],
        "delivered_days_ago": 10,
    },
    "0003": {
        "email": "basia@example.com",
        "status": "Delivered",
        "estimated_delivery": None,
        "items": ["Sapiens"],
        "delivered_days_ago": 45,
    },
}


# Tool 1: Get Order Status

def get_order_status(order_id: str):
    """
    Returns order status details.
    """
    order = ORDERS.get(order_id)

    if not order:
        return {
            "success": False,
            "message": "Order not found."
        }

    return {
        "success": True,
        "order_id": order_id,
        "status": order["status"],
        "estimated_delivery": order["estimated_delivery"],
        "items": order["items"]
    }



# Tool 2: Check Return Eligibility

def check_return_eligibility(order_id: str):
    """
    Returns whether an order is eligible for return.
    Policy: must be delivered within 30 days.
    """
    order = ORDERS.get(order_id)

    if not order:
        return {
            "success": False,
            "message": "Order not found."
        }

    if order["status"] != "Delivered":
        return {
            "success": True,
            "eligible": False,
            "reason": "Order has not been delivered yet."
        }

    if order["delivered_days_ago"] is None:
        return {
            "success": True,
            "eligible": False,
            "reason": "Delivery date unknown."
        }

    if order["delivered_days_ago"] <= 30:
        return {
            "success": True,
            "eligible": True,
            "items": order["items"]
        }

    return {
        "success": True,
        "eligible": False,
        "reason": "Return window (30 days) has expired."
    }



# Tool 3: Create Return Request

def create_return_request(order_id: str, item: str, reason: str):
    """
    Simulates creating a return request.
    """
    order = ORDERS.get(order_id)

    if not order:
        return {
            "success": False,
            "message": "Order not found."
        }

    if item not in order["items"]:
        return {
            "success": False,
            "message": "Item not found in order."
        }

    # Generate fake return ID
    return_id = f"RET-{order_id}-{int(datetime.now().timestamp())}"

    return {
        "success": True,
        "return_id": return_id,
        "item": item,
        "reason": reason,
        "message": "Return request created successfully."
    }