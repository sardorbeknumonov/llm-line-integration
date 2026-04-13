"""Tests for the tool call handler — full Margaret ordering scenario."""

from app.handlers.tool_call_handler import handle_tool_call, _carts, _orders, _user_orders


USER_ID = "test_margaret"


class TestGetFoodCategories:
    def test_returns_four_categories(self):
        r = handle_tool_call("get_food_categories", {"user_id": USER_ID})
        assert len(r["categories"]) == 4

    def test_category_keys(self):
        r = handle_tool_call("get_food_categories", {"user_id": USER_ID})
        keys = [c["key"] for c in r["categories"]]
        assert keys == ["noodles", "rice", "fastfood", "healthy"]

    def test_each_category_has_image(self):
        r = handle_tool_call("get_food_categories", {"user_id": USER_ID})
        for cat in r["categories"]:
            assert cat["image_url"].startswith("https://")


class TestSearchRestaurants:
    def test_noodles_returns_three(self):
        r = handle_tool_call("search_restaurants", {"category": "noodles"})
        assert len(r["restaurants"]) == 3

    def test_each_category_has_restaurants(self):
        for cat in ("noodles", "rice", "fastfood", "healthy"):
            r = handle_tool_call("search_restaurants", {"category": cat})
            assert len(r["restaurants"]) == 3
            assert r["category"] == cat

    def test_restaurant_fields(self):
        r = handle_tool_call("search_restaurants", {"category": "noodles"})
        rest = r["restaurants"][0]
        assert rest["id"] == "noodle-1"
        assert rest["name"] == "Uncle Sam's Noodle House"
        assert rest["rating"] == 4.8
        assert rest["delivery_time_min"] == 20
        assert rest["price_from"] == 6.00

    def test_invalid_category(self):
        r = handle_tool_call("search_restaurants", {"category": "pizza"})
        assert "error" in r


class TestGetRestaurantMenu:
    def test_noodle_1_menu(self):
        r = handle_tool_call("get_restaurant_menu", {"restaurant_id": "noodle-1"})
        assert r["restaurant_name"] == "Uncle Sam's Noodle House"
        assert len(r["items"]) == 3

    def test_menu_item_fields(self):
        r = handle_tool_call("get_restaurant_menu", {"restaurant_id": "noodle-1"})
        item = r["items"][1]  # Large Pork Noodle Soup
        assert item["id"] == "n1-2"
        assert item["price"] == 8.00
        assert item["image_url"].startswith("https://")

    def test_all_restaurants_have_menus(self):
        for rid in ("noodle-1", "noodle-2", "noodle-3", "rice-1", "rice-2", "rice-3",
                     "fast-1", "fast-2", "fast-3", "health-1", "health-2", "health-3"):
            r = handle_tool_call("get_restaurant_menu", {"restaurant_id": rid})
            assert "items" in r, f"No menu for {rid}"
            assert len(r["items"]) == 3

    def test_invalid_restaurant(self):
        r = handle_tool_call("get_restaurant_menu", {"restaurant_id": "fake"})
        assert "error" in r


class TestAddToCart:
    def setup_method(self):
        _carts.pop(USER_ID, None)

    def test_add_item(self):
        r = handle_tool_call("add_to_cart", {
            "user_id": USER_ID,
            "restaurant_id": "noodle-1",
            "item_id": "n1-2",
            "quantity": 1,
        })
        assert r["added"]["name"] == "Classic Pork Noodle Soup (Large)"
        assert r["added"]["price"] == 8.00
        assert r["cart_count"] == 1
        assert r["total"] == 10.50  # 8.00 + 2.50 delivery

    def test_add_with_special_request(self):
        r = handle_tool_call("add_to_cart", {
            "user_id": USER_ID,
            "restaurant_id": "noodle-1",
            "item_id": "n1-3",
            "quantity": 1,
            "special_requests": "extra spicy",
        })
        assert r["added"]["special_requests"] == "extra spicy"

    def test_add_multiple_items(self):
        handle_tool_call("add_to_cart", {
            "user_id": USER_ID, "restaurant_id": "noodle-1", "item_id": "n1-1", "quantity": 1,
        })
        r = handle_tool_call("add_to_cart", {
            "user_id": USER_ID, "restaurant_id": "noodle-1", "item_id": "n1-3", "quantity": 1,
        })
        assert r["cart_count"] == 2
        assert r["total"] == 6.00 + 8.50 + 2.50  # subtotal + delivery

    def test_invalid_restaurant(self):
        r = handle_tool_call("add_to_cart", {
            "user_id": USER_ID, "restaurant_id": "fake", "item_id": "x", "quantity": 1,
        })
        assert "error" in r

    def test_invalid_item(self):
        r = handle_tool_call("add_to_cart", {
            "user_id": USER_ID, "restaurant_id": "noodle-1", "item_id": "fake", "quantity": 1,
        })
        assert "error" in r


class TestGetOrderSummary:
    def setup_method(self):
        _carts.pop(USER_ID, None)

    def test_empty_cart(self):
        r = handle_tool_call("get_order_summary", {"user_id": USER_ID})
        assert "error" in r

    def test_summary_with_item(self):
        handle_tool_call("add_to_cart", {
            "user_id": USER_ID, "restaurant_id": "noodle-1", "item_id": "n1-2", "quantity": 1,
        })
        r = handle_tool_call("get_order_summary", {"user_id": USER_ID})
        assert r["total"] == 10.50
        assert r["subtotal"] == 8.00
        assert r["delivery_fee"] == 2.50
        assert r["delivery_address"] == "Margaret's Home (saved address)"
        assert len(r["payment_options"]) == 3


class TestFullOrderFlow:
    """Test the complete Margaret scenario end-to-end."""

    def setup_method(self):
        _carts.pop(USER_ID, None)
        _user_orders.pop(USER_ID, None)

    def test_full_scenario(self):
        # Act 1: Browse → Add to cart
        handle_tool_call("add_to_cart", {
            "user_id": USER_ID, "restaurant_id": "noodle-1", "item_id": "n1-2", "quantity": 1,
        })

        # Act 2: Place order
        r = handle_tool_call("place_order", {"user_id": USER_ID})
        assert r["status"] == "pending_payment"
        order_id = r["order_id"]
        assert order_id.startswith("ORD-")

        # Initiate payment
        r = handle_tool_call("initiate_payment", {
            "user_id": USER_ID, "order_id": order_id, "payment_method": "line_pay",
        })
        assert r["status"] == "awaiting_payment"
        assert r["payment_url"] is not None
        txn_id = r["transaction_id"]

        # Confirm payment
        r = handle_tool_call("confirm_payment", {
            "user_id": USER_ID, "order_id": order_id, "transaction_id": txn_id,
        })
        assert r["status"] == "confirmed"
        assert r["amount_charged"] == 10.50
        assert r["payment_method"] == "line_pay"

        # Cart should be cleared
        r = handle_tool_call("get_order_summary", {"user_id": USER_ID})
        assert "error" in r

        # Act 3: Track order
        r = handle_tool_call("get_order_status", {"user_id": USER_ID})
        assert r["order_id"] == order_id
        assert r["status"] == "confirmed"

        r = handle_tool_call("track_rider", {"user_id": USER_ID})
        assert r["rider"]["name"] == "James"
        assert r["estimated_arrival_min"] == 8

        # Act 4: Review
        r = handle_tool_call("submit_review", {
            "user_id": USER_ID, "rating": 5, "tags": ["Delicious!", "Super fast"],
        })
        assert r["rating"] == 5
        assert r["tags"] == ["Delicious!", "Super fast"]
        assert r["status"] == "saved"


class TestPlaceOrder:
    def setup_method(self):
        _carts.pop(USER_ID, None)
        _user_orders.pop(USER_ID, None)

    def test_empty_cart(self):
        r = handle_tool_call("place_order", {"user_id": USER_ID})
        assert "error" in r

    def test_cash_payment(self):
        handle_tool_call("add_to_cart", {
            "user_id": USER_ID, "restaurant_id": "fast-1", "item_id": "f1-1", "quantity": 1,
        })
        r = handle_tool_call("place_order", {"user_id": USER_ID})
        order_id = r["order_id"]

        r = handle_tool_call("initiate_payment", {
            "user_id": USER_ID, "order_id": order_id, "payment_method": "cash",
        })
        assert r["payment_url"] is None  # No URL for cash


class TestUnknownTool:
    def test_unknown_tool(self):
        r = handle_tool_call("nonexistent_tool", {})
        assert "error" in r
        assert "available_tools" in r
