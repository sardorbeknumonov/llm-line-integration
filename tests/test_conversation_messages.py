"""Tests for conversation message builders."""

from app.models.menu import MenuItem, Restaurant
from app.builders.conversation_messages import (
    build_greeting,
    build_restaurant_list,
    build_menu_items,
    build_special_request_prompt,
    build_order_summary,
    build_payment_options,
    build_payment_success,
    build_order_cancelled,
    build_tracking_preparing,
    build_tracking_rider,
    build_tracking_delivered,
    build_review_rating_prompt,
    build_review_highlights_prompt,
    build_review_complete,
    build_order_history,
)


def _sample_restaurant() -> Restaurant:
    return Restaurant(
        id="test-1",
        name="Test Noodle Shop",
        image_url="https://example.com/img.jpg",
        rating=4.8,
        delivery_time_min=20,
        price_from=6.0,
        menu=[
            MenuItem(id="t1", name="Pork Noodle", price=6.0, image_url="https://example.com/pork.jpg", description="Tasty pork noodle"),
            MenuItem(id="t2", name="Beef Noodle", price=8.0, image_url="https://example.com/beef.jpg", description="Rich beef noodle"),
        ],
    )


class TestGreeting:
    def test_returns_text_with_quick_reply(self):
        msgs = build_greeting()
        assert len(msgs) == 1
        assert msgs[0]["type"] == "text"
        assert "quickReply" in msgs[0]
        assert len(msgs[0]["quickReply"]["items"]) == 4  # 4 categories


class TestRestaurantList:
    def test_returns_text_and_carousel(self):
        msgs = build_restaurant_list("noodles")
        assert len(msgs) == 2
        assert msgs[0]["type"] == "text"
        assert msgs[1]["type"] == "flex"
        assert msgs[1]["contents"]["type"] == "carousel"

    def test_carousel_has_3_restaurants(self):
        msgs = build_restaurant_list("noodles")
        bubbles = msgs[1]["contents"]["contents"]
        assert len(bubbles) == 3

    def test_invalid_category(self):
        msgs = build_restaurant_list("invalid")
        assert len(msgs) == 1
        assert "Sorry" in msgs[0]["text"]

    def test_restaurant_bubble_has_view_menu_button(self):
        msgs = build_restaurant_list("noodles")
        bubble = msgs[1]["contents"]["contents"][0]
        footer = bubble["footer"]["contents"][0]
        assert footer["action"]["type"] == "message"
        assert "View Menu" in footer["action"]["label"]

    def test_last_message_has_quick_replies(self):
        msgs = build_restaurant_list("noodles")
        assert "quickReply" in msgs[-1]


class TestMenuItems:
    def test_returns_text_and_carousel(self):
        r = _sample_restaurant()
        msgs = build_menu_items(r)
        assert len(msgs) == 2
        assert msgs[1]["type"] == "flex"

    def test_carousel_has_menu_items(self):
        r = _sample_restaurant()
        msgs = build_menu_items(r)
        bubbles = msgs[1]["contents"]["contents"]
        assert len(bubbles) == 2  # 2 menu items

    def test_menu_bubble_has_order_button(self):
        r = _sample_restaurant()
        msgs = build_menu_items(r)
        bubble = msgs[1]["contents"]["contents"][0]
        btn = bubble["footer"]["contents"][0]
        assert "Order" in btn["action"]["label"]
        assert btn["action"]["type"] == "message"

    def test_has_quick_replies(self):
        r = _sample_restaurant()
        msgs = build_menu_items(r)
        assert "quickReply" in msgs[-1]


class TestSpecialRequest:
    def test_prompt(self):
        msgs = build_special_request_prompt("Pork Noodle")
        assert len(msgs) == 1
        assert "Pork Noodle" in msgs[0]["text"]
        assert "quickReply" in msgs[0]


class TestOrderSummary:
    def test_returns_flex_bubble(self):
        item = MenuItem(id="t1", name="Pork Noodle", price=6.0)
        msgs = build_order_summary(item, "Test Shop")
        assert len(msgs) == 1
        assert msgs[0]["type"] == "flex"
        assert msgs[0]["contents"]["type"] == "bubble"

    def test_has_confirm_cancel_buttons(self):
        item = MenuItem(id="t1", name="Pork Noodle", price=6.0)
        msgs = build_order_summary(item, "Test Shop")
        footer = msgs[0]["contents"]["footer"]["contents"]
        # First: Confirm button, Second: box with Cancel + Change Address
        assert len(footer) == 2
        assert "Confirm" in footer[0]["action"]["label"]

    def test_includes_special_note(self):
        item = MenuItem(id="t1", name="Pork Noodle", price=6.0)
        msgs = build_order_summary(item, "Test Shop", special_note="No onions")
        body_texts = [c.get("text", "") for c in msgs[0]["contents"]["body"]["contents"]]
        assert any("No onions" in t for t in body_texts)


class TestPayment:
    def test_payment_options_has_3_choices(self):
        msgs = build_payment_options()
        assert "quickReply" in msgs[0]
        assert len(msgs[0]["quickReply"]["items"]) == 3

    def test_payment_success(self):
        msgs = build_payment_success("LINE Pay", "ORD-123")
        assert "ORD-123" in msgs[0]["text"]
        assert "successful" in msgs[0]["text"].lower()

    def test_order_cancelled(self):
        msgs = build_order_cancelled()
        assert "cancelled" in msgs[0]["text"].lower()


class TestTracking:
    def test_preparing(self):
        msgs = build_tracking_preparing("Test Shop")
        assert "Test Shop" in msgs[0]["text"]

    def test_rider(self):
        msgs = build_tracking_rider()
        assert "quickReply" in msgs[0]
        assert "rider" in msgs[0]["text"].lower()

    def test_delivered(self):
        msgs = build_tracking_delivered()
        assert "delivered" in msgs[0]["text"].lower()


class TestReview:
    def test_rating_prompt_has_5_options(self):
        msgs = build_review_rating_prompt()
        assert "quickReply" in msgs[0]
        assert len(msgs[0]["quickReply"]["items"]) == 5

    def test_highlights_prompt(self):
        msgs = build_review_highlights_prompt(5)
        assert "quickReply" in msgs[0]
        assert len(msgs[0]["quickReply"]["items"]) == 4

    def test_review_complete(self):
        msgs = build_review_complete()
        assert "quickReply" in msgs[0]
        items = msgs[0]["quickReply"]["items"]
        labels = [i["action"]["label"] for i in items]
        assert any("Order Again" in l for l in labels)

    def test_order_history(self):
        msgs = build_order_history("ORD-123", "Pork Noodle", 8.50)
        assert "ORD-123" in msgs[0]["text"]
        assert "Pork Noodle" in msgs[0]["text"]
