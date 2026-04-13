"""Tests for sendbird_message_converter using real AI Agent message payloads."""

import json
import pytest
from app.builders.sendbird_message_converter import convert_bot_message


# ── 1. Simple text (no payload) ─────────────────

def test_simple_text_no_payload():
    msgs = convert_bot_message("Hello! How can I help?")
    assert len(msgs) == 1
    assert msgs[0] == {"type": "text", "text": "Hello! How can I help?"}


def test_empty_text_no_payload():
    msgs = convert_bot_message("", None)
    assert msgs == []


# ── 2. get_food_categories → text + quick reply ─

def test_food_categories_with_suggested_replies():
    payload = {
        "function_calls": [{
            "name": "get_food_categories",
            "response": {
                "status_code": 200,
                "response_text": json.dumps({
                    "categories": [
                        {"key": "noodles", "label": "\U0001f35c Noodles"},
                        {"key": "rice", "label": "\U0001f371 Rice & Mains"},
                    ]
                }),
            },
        }],
        "suggested_replies": [
            "\U0001f35c Noodles",
            "\U0001f371 Rice & Mains",
            "\U0001f355 Fast Food",
            "\U0001f957 Healthy",
        ],
    }
    msgs = convert_bot_message("What are you in the mood for today?", payload)
    assert len(msgs) == 1
    assert msgs[0]["type"] == "text"
    assert "quickReply" in msgs[0]
    assert len(msgs[0]["quickReply"]["items"]) == 4


# ── 3. search_restaurants → flex carousel + quick reply ─

def test_search_restaurants_carousel():
    payload = {
        "function_calls": [{
            "name": "search_restaurants",
            "response": {
                "status_code": 200,
                "response_text": json.dumps({
                    "category": "fastfood",
                    "restaurants": [
                        {"id": "fast-1", "title": "Burger Lab", "image_url": "https://example.com/img.jpg", "description": "⭐ 4.6 · 15 min", "cta_label": "View Menu", "cta_url": ""},
                        {"id": "fast-2", "title": "Pizza Express", "image_url": "https://example.com/img2.jpg", "description": "⭐ 4.4 · 25 min", "cta_label": "View Menu", "cta_url": ""},
                    ]
                }),
            },
        }],
        "suggested_replies": ["Burger Lab", "Pizza Express"],
    }
    msgs = convert_bot_message("Here are fast food restaurants!", payload)

    assert len(msgs) == 2  # text + flex carousel
    assert msgs[0]["type"] == "text"
    assert msgs[1]["type"] == "flex"
    assert msgs[1]["contents"]["type"] == "carousel"
    assert len(msgs[1]["contents"]["contents"]) == 2  # 2 bubbles

    # Quick reply on last message
    assert "quickReply" in msgs[1]
    assert len(msgs[1]["quickReply"]["items"]) == 2

    # Verify bubble structure
    bubble = msgs[1]["contents"]["contents"][0]
    assert bubble["type"] == "bubble"
    assert "hero" in bubble
    assert bubble["hero"]["url"] == "https://example.com/img.jpg"


# ── 4. get_restaurant_menu → flex carousel with prices ─

def test_restaurant_menu_carousel():
    payload = {
        "function_calls": [{
            "name": "get_restaurant_menu",
            "response": {
                "status_code": 200,
                "response_text": json.dumps({
                    "restaurant_id": "fast-2",
                    "restaurant_name": "Pizza Express",
                    "items": [
                        {"id": "f2-1", "name": "Margherita Pizza", "price": 8.0, "description": "Fresh mozzarella", "image_url": "https://example.com/pizza.jpg"},
                        {"id": "f2-2", "name": "Pepperoni Pizza", "price": 10.0, "description": "Loaded with pepperoni", "image_url": ""},
                    ]
                }),
            },
        }],
        "suggested_replies": ["Margherita Pizza", "Pepperoni Pizza"],
    }
    msgs = convert_bot_message("Here's the menu!", payload)

    assert len(msgs) == 2
    assert msgs[1]["type"] == "flex"
    carousel = msgs[1]["contents"]
    assert carousel["type"] == "carousel"
    assert len(carousel["contents"]) == 2

    # First bubble has hero image, second doesn't
    assert "hero" in carousel["contents"][0]
    assert "hero" not in carousel["contents"][1]

    # Quick reply attached
    assert "quickReply" in msgs[1]


# ── 5. add_to_cart → text only ──────────────────

def test_add_to_cart_text():
    payload = {
        "function_calls": [{
            "name": "add_to_cart",
            "response": {
                "status_code": 200,
                "response_text": json.dumps({
                    "added": {"food_id": "f2-2", "name": "Pepperoni Pizza", "price": 10.0},
                    "cart_count": 1,
                    "subtotal": 10.0,
                    "total": 12.5,
                }),
            },
        }],
    }
    msgs = convert_bot_message("Pepperoni Pizza added to your cart!", payload)
    assert len(msgs) == 1
    assert msgs[0]["type"] == "text"
    assert "quickReply" not in msgs[0]  # no suggested_replies


# ── 6. get_order_summary → flex bubble ──────────

def test_order_summary_bubble():
    payload = {
        "function_calls": [{
            "name": "get_order_summary",
            "response": {
                "status_code": 200,
                "response_text": json.dumps({
                    "restaurant_name": "Pizza Express",
                    "items": [
                        {"name": "Pepperoni Pizza", "quantity": 1, "price": 10.0, "subtotal": 10.0, "special_requests": "More cheese"},
                    ],
                    "subtotal": 10.0,
                    "delivery_fee": 2.5,
                    "total": 12.5,
                    "estimated_delivery_min": 25,
                    "payment_options": [
                        {"key": "line_pay", "label": "LINE Pay"},
                    ],
                }),
            },
        }],
    }
    msgs = convert_bot_message("Here's your order summary!", payload)

    assert len(msgs) == 2  # text + flex bubble
    assert msgs[1]["type"] == "flex"
    assert msgs[1]["contents"]["type"] == "bubble"
    assert "$12.50" in msgs[1]["altText"]


# ── 7. initiate_payment → text + quick reply ────

def test_initiate_payment():
    payload = {
        "function_calls": [{
            "name": "initiate_payment",
            "response": {
                "status_code": 200,
                "response_text": json.dumps({
                    "order_id": "ORD-123",
                    "transaction_id": "TXN-456",
                    "payment_method": "line_pay",
                    "amount": 12.5,
                    "status": "awaiting_payment",
                }),
            },
        }],
        "suggested_replies": ["\U0001f49a LINE Pay", "\U0001f4b5 Cash", "\U0001f4b3 Credit Card"],
    }
    msgs = convert_bot_message("Choose your payment method:", payload)
    assert len(msgs) == 1
    assert msgs[0]["type"] == "text"
    assert "quickReply" in msgs[0]
    assert len(msgs[0]["quickReply"]["items"]) == 3


# ── 8. confirm_payment → text + flex bubble ─────

def test_confirm_payment_bubble():
    payload = {
        "function_calls": [{
            "name": "confirm_payment",
            "response": {
                "status_code": 200,
                "response_text": json.dumps({
                    "order_id": "ORD-123",
                    "transaction_id": "TXN-456",
                    "status": "confirmed",
                    "amount_charged": 12.5,
                    "payment_method": "line_pay",
                    "restaurant_name": "Pizza Express",
                    "estimated_delivery_min": 25,
                }),
            },
        }],
    }
    msgs = convert_bot_message("Payment successful!", payload)

    assert len(msgs) == 2
    assert msgs[1]["type"] == "flex"
    assert msgs[1]["contents"]["type"] == "bubble"
    assert "ORD-123" in msgs[1]["altText"]


# ── 9. get_order_status → flex bubble with timeline ─

def test_order_status_timeline():
    payload = {
        "function_calls": [{
            "name": "get_order_status",
            "response": {
                "status_code": 200,
                "response_text": json.dumps({
                    "order_id": "ORD-123",
                    "status": "confirmed",
                    "restaurant_name": "Pizza Express",
                    "estimated_delivery_min": 25,
                    "timeline": [
                        {"status": "confirmed", "label": "Order Confirmed", "completed": True},
                        {"status": "preparing", "label": "Preparing", "completed": False},
                    ],
                }),
            },
        }],
    }
    msgs = convert_bot_message("Here's your order status:", payload)
    assert len(msgs) == 2
    assert msgs[1]["type"] == "flex"
    assert msgs[1]["contents"]["type"] == "bubble"


# ── 10. No function_calls, just suggested_replies ─

def test_text_with_suggested_replies_only():
    payload = {
        "bot_message_type": "generated",
        "is_last_in_turn": True,
        "suggested_replies": ["Yes", "No", "Cancel"],
    }
    msgs = convert_bot_message("Would you like to proceed?", payload)
    assert len(msgs) == 1
    assert msgs[0]["type"] == "text"
    assert "quickReply" in msgs[0]
    assert len(msgs[0]["quickReply"]["items"]) == 3
