"""Tests for message converter — AI Agent data → LINE messages."""

import json

from app.builders.message_converter import convert_to_line_messages


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PLAIN TEXT (no data)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_plain_text_no_data():
    msgs = convert_to_line_messages("Hello there!", None)
    assert len(msgs) == 1
    assert msgs[0]["type"] == "text"
    assert msgs[0]["text"] == "Hello there!"


def test_plain_text_empty_data():
    msgs = convert_to_line_messages("Hello!", "")
    assert len(msgs) == 1
    assert msgs[0]["type"] == "text"


def test_empty_content_no_data():
    msgs = convert_to_line_messages("", None)
    assert msgs == []


def test_invalid_json_data_falls_back_to_text():
    msgs = convert_to_line_messages("Fallback text", "not-valid-json")
    assert len(msgs) == 1
    assert msgs[0]["type"] == "text"
    assert msgs[0]["text"] == "Fallback text"


def test_unknown_type_falls_back_to_text():
    data = json.dumps({"type": "unknown_type", "foo": "bar"})
    msgs = convert_to_line_messages("Some text", data)
    assert len(msgs) == 1
    assert msgs[0]["type"] == "text"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FOOD CAROUSEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_food_carousel_basic():
    data = json.dumps({
        "type": "food_carousel",
        "items": [
            {
                "food_id": "FC001",
                "name": "Spicy Chicken",
                "restaurant": "BBQ Place",
                "price": 15.99,
                "image_url": "https://example.com/chicken.jpg",
                "rating": 4.5,
                "delivery_time_min": 25,
            },
            {
                "food_id": "FC002",
                "name": "Buffalo Wings",
                "restaurant": "Wing Zone",
                "price": 11.99,
                "image_url": "https://example.com/wings.jpg",
                "rating": 4.3,
                "delivery_time_min": 20,
            },
        ],
    })
    msgs = convert_to_line_messages("Here are some options!", data)

    # Should be: [text header, flex carousel]
    assert len(msgs) == 2
    assert msgs[0]["type"] == "text"
    assert msgs[0]["text"] == "Here are some options!"
    assert msgs[1]["type"] == "flex"
    assert msgs[1]["contents"]["type"] == "carousel"
    assert len(msgs[1]["contents"]["contents"]) == 2


def test_food_carousel_with_header_text():
    data = json.dumps({
        "type": "food_carousel",
        "header_text": "Top picks for you!",
        "items": [
            {"name": "Pizza", "restaurant": "Pizza Hut", "price": 10.0},
        ],
    })
    msgs = convert_to_line_messages("", data)

    assert len(msgs) == 2
    assert msgs[0]["text"] == "Top picks for you!"


def test_food_carousel_empty_items():
    data = json.dumps({"type": "food_carousel", "items": []})
    msgs = convert_to_line_messages("No items found", data)

    assert len(msgs) == 1
    assert msgs[0]["type"] == "text"


def test_food_carousel_max_12_items():
    items = [{"name": f"Food {i}", "price": 10.0} for i in range(15)]
    data = json.dumps({"type": "food_carousel", "items": items})
    msgs = convert_to_line_messages("Lots of food!", data)

    carousel = msgs[1]["contents"]
    assert len(carousel["contents"]) == 12  # LINE max


def test_food_bubble_has_message_buttons():
    """Buttons should use LINE message action (not postback) for middleware pattern."""
    data = json.dumps({
        "type": "food_carousel",
        "items": [
            {"name": "Spicy Chicken", "restaurant": "BBQ", "price": 15.0},
        ],
    })
    msgs = convert_to_line_messages("Check this out", data)

    bubble = msgs[1]["contents"]["contents"][0]
    footer_buttons = bubble["footer"]["contents"]

    # 3 buttons: Order, Add to Cart, Details
    assert len(footer_buttons) == 3
    for btn in footer_buttons:
        assert btn["action"]["type"] == "message"

    # Verify button texts
    assert "Order" in footer_buttons[0]["action"]["text"]
    assert "Add" in footer_buttons[1]["action"]["text"]
    assert "Tell me more" in footer_buttons[2]["action"]["text"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ORDER CONFIRMATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_order_confirmation():
    data = json.dumps({
        "type": "order_confirmation",
        "order_id": "ORD-ABC123",
        "items": [
            {"name": "Spicy Chicken", "qty": 2, "price": 15.99},
            {"name": "Buffalo Wings", "qty": 1, "price": 11.99},
        ],
        "total": 43.97,
        "delivery_min": 30,
        "status": "confirmed",
    })
    msgs = convert_to_line_messages("Your order is confirmed!", data)

    assert len(msgs) == 2
    assert msgs[0]["type"] == "text"
    assert msgs[1]["type"] == "flex"
    assert msgs[1]["contents"]["type"] == "bubble"


def test_order_confirmation_no_content():
    data = json.dumps({
        "type": "order_confirmation",
        "order_id": "ORD-XYZ",
        "total": 20.0,
    })
    msgs = convert_to_line_messages("", data)

    # No text header when content is empty
    assert len(msgs) == 1
    assert msgs[0]["type"] == "flex"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BUTTONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_buttons():
    data = json.dumps({
        "type": "buttons",
        "title": "What do you want?",
        "text": "Choose a category",
        "actions": [
            {"label": "Chicken", "text": "Show me chicken"},
            {"label": "Pizza", "text": "Show me pizza"},
            {"label": "Sushi", "text": "Show me sushi"},
        ],
    })
    msgs = convert_to_line_messages("Choose a category", data)

    # content == data.text, so no separate header
    assert any(m["type"] == "flex" for m in msgs)

    flex = [m for m in msgs if m["type"] == "flex"][0]
    bubble = flex["contents"]
    assert bubble["type"] == "bubble"
    assert len(bubble["footer"]["contents"]) == 3


def test_buttons_empty_actions_falls_back():
    data = json.dumps({"type": "buttons", "title": "Empty", "actions": []})
    msgs = convert_to_line_messages("Fallback", data)

    assert len(msgs) == 1
    assert msgs[0]["type"] == "text"


def test_buttons_with_image():
    data = json.dumps({
        "type": "buttons",
        "title": "Special Offer",
        "text": "50% off!",
        "image_url": "https://example.com/promo.jpg",
        "actions": [{"label": "Order Now", "text": "Order the special"}],
    })
    msgs = convert_to_line_messages("", data)

    flex = [m for m in msgs if m["type"] == "flex"][0]
    assert "hero" in flex["contents"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  QUICK REPLY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_quick_reply():
    data = json.dumps({
        "type": "quick_reply",
        "text": "How spicy?",
        "options": ["Mild", "Medium", "Hot"],
    })
    msgs = convert_to_line_messages("", data)

    assert len(msgs) == 1
    assert msgs[0]["type"] == "text"
    assert msgs[0]["text"] == "How spicy?"
    assert "quickReply" in msgs[0]
    assert len(msgs[0]["quickReply"]["items"]) == 3

    # Verify each option
    for i, item in enumerate(msgs[0]["quickReply"]["items"]):
        assert item["action"]["type"] == "message"


def test_quick_reply_empty_options_falls_back():
    data = json.dumps({"type": "quick_reply", "text": "Choose", "options": []})
    msgs = convert_to_line_messages("Choose something", data)

    assert len(msgs) == 1
    assert msgs[0]["type"] == "text"
    assert "quickReply" not in msgs[0]


def test_quick_reply_max_13_options():
    data = json.dumps({
        "type": "quick_reply",
        "text": "Pick one",
        "options": [f"Option {i}" for i in range(20)],
    })
    msgs = convert_to_line_messages("", data)

    assert len(msgs[0]["quickReply"]["items"]) == 13  # LINE max
