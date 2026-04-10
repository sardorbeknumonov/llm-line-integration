"""Tests for Flex Carousel builders."""

from app.models.messages import FoodItemData, OrderConfirmationData, OrderItemData, ButtonsData, ButtonAction
from app.builders.flex_carousel import (
    build_food_bubble,
    build_food_carousel,
    build_order_confirmation_bubble,
    build_buttons_bubble,
)


def _sample_food() -> FoodItemData:
    return FoodItemData(
        food_id="TEST001",
        name="Test Chicken",
        restaurant="Test Restaurant",
        price=12.99,
        image_url="https://example.com/test.jpg",
        rating=4.5,
        description="A test food item",
        delivery_time_min=25,
    )


def test_build_food_bubble_structure():
    item = _sample_food()
    bubble = build_food_bubble(item)

    assert bubble["type"] == "bubble"
    assert bubble["size"] == "kilo"
    assert "hero" in bubble  # has image_url
    assert "body" in bubble
    assert "footer" in bubble


def test_build_food_bubble_no_image():
    item = FoodItemData(name="No Image Food", price=5.0)
    bubble = build_food_bubble(item)

    assert "hero" not in bubble  # no image_url


def test_build_food_bubble_hero_image():
    item = _sample_food()
    bubble = build_food_bubble(item)

    hero = bubble["hero"]
    assert hero["type"] == "image"
    assert hero["url"] == item.image_url


def test_build_food_bubble_has_three_buttons():
    item = _sample_food()
    bubble = build_food_bubble(item)

    footer_buttons = bubble["footer"]["contents"]
    assert len(footer_buttons) == 3  # Order, Add to Cart, Details


def test_build_food_bubble_uses_message_actions():
    """In middleware pattern, buttons use message action (not postback)."""
    item = _sample_food()
    bubble = build_food_bubble(item)

    for btn in bubble["footer"]["contents"]:
        assert btn["action"]["type"] == "message"


def test_build_food_bubble_button_texts():
    item = _sample_food()
    bubble = build_food_bubble(item)

    buttons = bubble["footer"]["contents"]
    assert "Order" in buttons[0]["action"]["text"]
    assert "Test Restaurant" in buttons[0]["action"]["text"]
    assert "Add" in buttons[1]["action"]["text"]
    assert "Tell me more" in buttons[2]["action"]["text"]


def test_build_food_carousel():
    items = [_sample_food() for _ in range(5)]
    carousel = build_food_carousel(items)

    assert carousel["type"] == "carousel"
    assert len(carousel["contents"]) == 5


def test_build_food_carousel_max_12():
    items = [_sample_food() for _ in range(15)]
    carousel = build_food_carousel(items)

    assert len(carousel["contents"]) == 12


def test_build_order_confirmation_bubble():
    order = OrderConfirmationData(
        order_id="ORD-TEST",
        items=[
            OrderItemData(name="Chicken", qty=2, price=15.0),
            OrderItemData(name="Wings", qty=1, price=12.0),
        ],
        total=42.0,
        delivery_min=25,
        status="confirmed",
    )
    bubble = build_order_confirmation_bubble(order)

    assert bubble["type"] == "bubble"
    assert "body" in bubble
    assert "footer" in bubble

    # Footer has Track Order button
    footer_btns = bubble["footer"]["contents"]
    assert len(footer_btns) == 1
    assert "Track" in footer_btns[0]["action"]["label"]


def test_build_buttons_bubble():
    data = ButtonsData(
        title="Pick a category",
        text="What are you craving?",
        actions=[
            ButtonAction(label="Chicken", text="Show me chicken"),
            ButtonAction(label="Pizza", text="Show me pizza"),
        ],
    )
    bubble = build_buttons_bubble(data)

    assert bubble["type"] == "bubble"
    assert len(bubble["footer"]["contents"]) == 2


def test_build_buttons_bubble_with_image():
    data = ButtonsData(
        title="Promo",
        image_url="https://example.com/promo.jpg",
        actions=[ButtonAction(label="Go", text="Order promo")],
    )
    bubble = build_buttons_bubble(data)

    assert "hero" in bubble
    assert bubble["hero"]["url"] == "https://example.com/promo.jpg"
