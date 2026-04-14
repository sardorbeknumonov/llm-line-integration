"""Mock tool call handler for LLM food ordering system.

Single dispatch: receives {"tool": "<name>", "arguments": {...}}
and returns a mock JSON response matching the Margaret ordering scenario.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

# ── In-memory state per user ───────────────────────

_carts: dict[str, list[dict]] = {}       # user_id -> cart items
_orders: dict[str, dict] = {}            # order_id -> order
_user_orders: dict[str, str] = {}        # user_id -> latest order_id

# ── Tool registry ─────────────────────────────────

_TOOLS: dict[str, callable] = {}


def _register(name: str):
    def decorator(fn):
        _TOOLS[name] = fn
        return fn
    return decorator


def handle_tool_call(tool: str, arguments: dict) -> dict:
    """Dispatch a tool call and return the mock response."""
    handler = _TOOLS.get(tool)
    if not handler:
        return {"error": f"Unknown tool: {tool}", "available_tools": list(_TOOLS.keys())}
    return handler(arguments)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACT 1 — Browsing & Selecting Food
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def clear_user_state(user_id: str) -> None:
    """Clear cart and order state for a user. Called when conversation closes."""
    _carts.pop(user_id, None)
    _user_orders.pop(user_id, None)


@_register("get_food_categories")
def get_food_categories(args: dict) -> dict:
    """Return available food categories."""
    return {
        "categories": [
            {
                "key": "noodles",
                "label": "🍜 Noodles",
                "image_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=300&fit=crop",
            },
            {
                "key": "rice",
                "label": "🍱 Rice & Mains",
                "image_url": "https://images.unsplash.com/photo-1512058564366-18510be2db19?w=400&h=300&fit=crop",
            },
            {
                "key": "fastfood",
                "label": "🍕 Fast Food",
                "image_url": "https://images.unsplash.com/photo-1561758033-d89a9ad46330?w=400&h=300&fit=crop",
            },
            {
                "key": "healthy",
                "label": "🥗 Healthy",
                "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop",
            },
        ],
    }


_RESTAURANTS = {
    "noodles": [
        {
            "id": "noodle-1",
            "name": "Uncle Sam's Noodle House",
            "image_url": "https://images.unsplash.com/photo-1555126634-323283e090fa?w=400&h=300&fit=crop",
            "rating": 4.8,
            "delivery_time_min": 20,
            "price_from": 6.00,
            "category": "noodles",
        },
        {
            "id": "noodle-2",
            "name": "Mama Chen's Noodles",
            "image_url": "https://images.unsplash.com/photo-1552611052-33e04de1b100?w=400&h=300&fit=crop",
            "rating": 4.6,
            "delivery_time_min": 35,
            "price_from": 5.50,
            "category": "noodles",
        },
        {
            "id": "noodle-3",
            "name": "Old Town Beef Noodles",
            "image_url": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=400&h=300&fit=crop",
            "rating": 4.7,
            "delivery_time_min": 25,
            "price_from": 7.00,
            "category": "noodles",
        },
    ],
    "rice": [
        {
            "id": "rice-1",
            "name": "Thai Basil Kitchen",
            "image_url": "https://images.unsplash.com/photo-1562565652-a0d8f0c59eb4?w=400&h=300&fit=crop",
            "rating": 4.7,
            "delivery_time_min": 25,
            "price_from": 7.50,
            "category": "rice",
        },
        {
            "id": "rice-2",
            "name": "Seoul Kitchen",
            "image_url": "https://images.unsplash.com/photo-1553163147-622ab57be1c7?w=400&h=300&fit=crop",
            "rating": 4.5,
            "delivery_time_min": 30,
            "price_from": 8.00,
            "category": "rice",
        },
        {
            "id": "rice-3",
            "name": "Hainanese Delight",
            "image_url": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400&h=300&fit=crop",
            "rating": 4.8,
            "delivery_time_min": 20,
            "price_from": 6.50,
            "category": "rice",
        },
    ],
    "fastfood": [
        {
            "id": "fast-1",
            "name": "Burger Lab",
            "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop",
            "rating": 4.6,
            "delivery_time_min": 15,
            "price_from": 6.00,
            "category": "fastfood",
        },
        {
            "id": "fast-2",
            "name": "Pizza Express",
            "image_url": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=300&fit=crop",
            "rating": 4.4,
            "delivery_time_min": 25,
            "price_from": 8.00,
            "category": "fastfood",
        },
        {
            "id": "fast-3",
            "name": "Fried Chicken Co.",
            "image_url": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=400&h=300&fit=crop",
            "rating": 4.5,
            "delivery_time_min": 20,
            "price_from": 5.50,
            "category": "fastfood",
        },
    ],
    "healthy": [
        {
            "id": "health-1",
            "name": "Green Bowl",
            "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop",
            "rating": 4.7,
            "delivery_time_min": 20,
            "price_from": 8.00,
            "category": "healthy",
        },
        {
            "id": "health-2",
            "name": "Poke Paradise",
            "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop",
            "rating": 4.6,
            "delivery_time_min": 25,
            "price_from": 9.00,
            "category": "healthy",
        },
        {
            "id": "health-3",
            "name": "Juice & Co.",
            "image_url": "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?w=400&h=300&fit=crop",
            "rating": 4.4,
            "delivery_time_min": 15,
            "price_from": 5.00,
            "category": "healthy",
        },
    ],
}


@_register("search_restaurants")
def search_restaurants(args: dict) -> dict:
    """Return restaurants for a given category."""
    category = args.get("category", "")
    restaurants = _RESTAURANTS.get(category, [])
    if not restaurants:
        return {"error": f"No restaurants found for category '{category}'"}
    return {
        "category": category,
        "restaurants": restaurants,
    }


_MENUS = {
    "noodle-1": {
        "restaurant_id": "noodle-1",
        "restaurant_name": "Uncle Sam's Noodle House",
        "items": [
            {
                "id": "n1-1",
                "name": "Classic Pork Noodle Soup (Regular)",
                "price": 6.00,
                "description": "Slow-cooked pork broth with handmade noodles",
                "image_url": "https://images.unsplash.com/photo-1555126634-323283e090fa?w=400&h=300&fit=crop",
            },
            {
                "id": "n1-2",
                "name": "Classic Pork Noodle Soup (Large)",
                "price": 8.00,
                "description": "Large bowl with extra noodles and pork",
                "image_url": "https://images.unsplash.com/photo-1591814468924-caf88d1232e1?w=400&h=300&fit=crop",
            },
            {
                "id": "n1-3",
                "name": "Spicy Beef Noodles",
                "price": 8.50,
                "description": "Rich beef broth with chili oil and tender beef slices",
                "image_url": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=400&h=300&fit=crop",
            },
        ],
    },
    "noodle-2": {
        "restaurant_id": "noodle-2",
        "restaurant_name": "Mama Chen's Noodles",
        "items": [
            {
                "id": "n2-1",
                "name": "Wonton Noodle Soup",
                "price": 5.50,
                "description": "Shrimp wontons in clear broth with egg noodles",
                "image_url": "https://images.unsplash.com/photo-1552611052-33e04de1b100?w=400&h=300&fit=crop",
            },
            {
                "id": "n2-2",
                "name": "Dan Dan Noodles",
                "price": 7.00,
                "description": "Spicy sesame sauce with minced pork",
                "image_url": "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=400&h=300&fit=crop",
            },
            {
                "id": "n2-3",
                "name": "Chicken Noodle Soup",
                "price": 6.50,
                "description": "Comfort classic with herbs and vegetables",
                "image_url": "https://images.unsplash.com/photo-1604152135912-04a022e23696?w=400&h=300&fit=crop",
            },
        ],
    },
    "noodle-3": {
        "restaurant_id": "noodle-3",
        "restaurant_name": "Old Town Beef Noodles",
        "items": [
            {
                "id": "n3-1",
                "name": "Braised Beef Noodles",
                "price": 9.00,
                "description": "8-hour braised beef in aromatic broth",
                "image_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=300&fit=crop",
            },
            {
                "id": "n3-2",
                "name": "Tomato Beef Noodles",
                "price": 8.50,
                "description": "Tangy tomato broth with tender beef chunks",
                "image_url": "https://images.unsplash.com/photo-1555126634-323283e090fa?w=400&h=300&fit=crop",
            },
            {
                "id": "n3-3",
                "name": "Dry Tossed Noodles",
                "price": 7.00,
                "description": "Chewy noodles with sesame and soy glaze",
                "image_url": "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=400&h=300&fit=crop",
            },
        ],
    },
    "rice-1": {
        "restaurant_id": "rice-1",
        "restaurant_name": "Thai Basil Kitchen",
        "items": [
            {
                "id": "r1-1",
                "name": "Pad Kra Pao (Basil Chicken Rice)",
                "price": 7.50,
                "description": "Stir-fried chicken with holy basil and fried egg",
                "image_url": "https://images.unsplash.com/photo-1562565652-a0d8f0c59eb4?w=400&h=300&fit=crop",
            },
            {
                "id": "r1-2",
                "name": "Green Curry with Rice",
                "price": 9.00,
                "description": "Creamy coconut green curry with jasmine rice",
                "image_url": "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=400&h=300&fit=crop",
            },
            {
                "id": "r1-3",
                "name": "Mango Sticky Rice",
                "price": 5.00,
                "description": "Sweet sticky rice with fresh mango",
                "image_url": "https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?w=400&h=300&fit=crop",
            },
        ],
    },
    "rice-2": {
        "restaurant_id": "rice-2",
        "restaurant_name": "Seoul Kitchen",
        "items": [
            {
                "id": "r2-1",
                "name": "Bibimbap",
                "price": 9.50,
                "description": "Mixed rice bowl with vegetables, beef, and gochujang",
                "image_url": "https://images.unsplash.com/photo-1553163147-622ab57be1c7?w=400&h=300&fit=crop",
            },
            {
                "id": "r2-2",
                "name": "Kimchi Fried Rice",
                "price": 8.00,
                "description": "Spicy kimchi fried rice with pork and egg",
                "image_url": "https://images.unsplash.com/photo-1512058564366-18510be2db19?w=400&h=300&fit=crop",
            },
            {
                "id": "r2-3",
                "name": "Bulgogi Rice Bowl",
                "price": 10.00,
                "description": "Marinated beef with pickled vegetables",
                "image_url": "https://images.unsplash.com/photo-1590301157890-4810ed352733?w=400&h=300&fit=crop",
            },
        ],
    },
    "rice-3": {
        "restaurant_id": "rice-3",
        "restaurant_name": "Hainanese Delight",
        "items": [
            {
                "id": "r3-1",
                "name": "Hainanese Chicken Rice",
                "price": 6.50,
                "description": "Poached chicken with fragrant rice and 3 sauces",
                "image_url": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400&h=300&fit=crop",
            },
            {
                "id": "r3-2",
                "name": "Roasted Chicken Rice",
                "price": 7.00,
                "description": "Crispy-skin roasted chicken on oiled rice",
                "image_url": "https://images.unsplash.com/photo-1598515214211-89d3c73ae83b?w=400&h=300&fit=crop",
            },
            {
                "id": "r3-3",
                "name": "Chicken Chop Rice",
                "price": 8.50,
                "description": "Golden fried chicken cutlet with gravy",
                "image_url": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=400&h=300&fit=crop",
            },
        ],
    },
    "fast-1": {
        "restaurant_id": "fast-1",
        "restaurant_name": "Burger Lab",
        "items": [
            {
                "id": "f1-1",
                "name": "Classic Smash Burger",
                "price": 6.00,
                "description": "Double patty with American cheese and secret sauce",
                "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop",
            },
            {
                "id": "f1-2",
                "name": "BBQ Bacon Burger",
                "price": 8.50,
                "description": "Smoky BBQ sauce, crispy bacon, cheddar",
                "image_url": "https://images.unsplash.com/photo-1553979459-d2229ba7433b?w=400&h=300&fit=crop",
            },
            {
                "id": "f1-3",
                "name": "Chicken Burger",
                "price": 7.00,
                "description": "Crispy fried chicken fillet with mayo",
                "image_url": "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=400&h=300&fit=crop",
            },
        ],
    },
    "fast-2": {
        "restaurant_id": "fast-2",
        "restaurant_name": "Pizza Express",
        "items": [
            {
                "id": "f2-1",
                "name": "Margherita Pizza",
                "price": 8.00,
                "description": "Fresh mozzarella, tomato sauce, basil",
                "image_url": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=300&fit=crop",
            },
            {
                "id": "f2-2",
                "name": "Pepperoni Pizza",
                "price": 10.00,
                "description": "Loaded with spicy pepperoni and cheese",
                "image_url": "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=400&h=300&fit=crop",
            },
            {
                "id": "f2-3",
                "name": "Hawaiian Pizza",
                "price": 9.50,
                "description": "Ham and pineapple on mozzarella",
                "image_url": "https://images.unsplash.com/photo-1565299507177-b0ac66763828?w=400&h=300&fit=crop",
            },
        ],
    },
    "fast-3": {
        "restaurant_id": "fast-3",
        "restaurant_name": "Fried Chicken Co.",
        "items": [
            {
                "id": "f3-1",
                "name": "3pc Fried Chicken",
                "price": 5.50,
                "description": "Golden crispy fried chicken pieces",
                "image_url": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=400&h=300&fit=crop",
            },
            {
                "id": "f3-2",
                "name": "Spicy Wings (6pc)",
                "price": 6.50,
                "description": "Hot & spicy wings with dipping sauce",
                "image_url": "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=400&h=300&fit=crop",
            },
            {
                "id": "f3-3",
                "name": "Chicken Tenders Meal",
                "price": 7.50,
                "description": "Crispy tenders with fries and coleslaw",
                "image_url": "https://images.unsplash.com/photo-1562967914-608f82629710?w=400&h=300&fit=crop",
            },
        ],
    },
    "health-1": {
        "restaurant_id": "health-1",
        "restaurant_name": "Green Bowl",
        "items": [
            {
                "id": "h1-1",
                "name": "Quinoa Power Bowl",
                "price": 9.50,
                "description": "Quinoa, avocado, roasted veggies, tahini",
                "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop",
            },
            {
                "id": "h1-2",
                "name": "Grilled Chicken Salad",
                "price": 8.00,
                "description": "Mixed greens with grilled chicken and vinaigrette",
                "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop",
            },
            {
                "id": "h1-3",
                "name": "Acai Smoothie Bowl",
                "price": 7.50,
                "description": "Acai blend topped with granola and fresh fruit",
                "image_url": "https://images.unsplash.com/photo-1590301157890-4810ed352733?w=400&h=300&fit=crop",
            },
        ],
    },
    "health-2": {
        "restaurant_id": "health-2",
        "restaurant_name": "Poke Paradise",
        "items": [
            {
                "id": "h2-1",
                "name": "Salmon Poke Bowl",
                "price": 11.00,
                "description": "Fresh salmon, edamame, avocado, sushi rice",
                "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop",
            },
            {
                "id": "h2-2",
                "name": "Tuna Poke Bowl",
                "price": 10.50,
                "description": "Ahi tuna with mango salsa and sesame",
                "image_url": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=400&h=300&fit=crop",
            },
            {
                "id": "h2-3",
                "name": "Tofu Poke Bowl",
                "price": 9.00,
                "description": "Crispy tofu, cucumber, pickled ginger",
                "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop",
            },
        ],
    },
    "health-3": {
        "restaurant_id": "health-3",
        "restaurant_name": "Juice & Co.",
        "items": [
            {
                "id": "h3-1",
                "name": "Green Detox Smoothie",
                "price": 6.00,
                "description": "Kale, spinach, apple, ginger, lemon",
                "image_url": "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?w=400&h=300&fit=crop",
            },
            {
                "id": "h3-2",
                "name": "Protein Shake",
                "price": 7.00,
                "description": "Banana, peanut butter, whey protein, oat milk",
                "image_url": "https://images.unsplash.com/photo-1553530666-ba11a7da3888?w=400&h=300&fit=crop",
            },
            {
                "id": "h3-3",
                "name": "Avocado Toast",
                "price": 5.00,
                "description": "Sourdough with smashed avocado and poached egg",
                "image_url": "https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?w=400&h=300&fit=crop",
            },
        ],
    },
}


@_register("get_restaurant_menu")
def get_restaurant_menu(args: dict) -> dict:
    """Return menu items for a given restaurant."""
    restaurant_id = args.get("restaurant_id", "")
    menu = _MENUS.get(restaurant_id)
    if not menu:
        return {"error": f"Restaurant '{restaurant_id}' not found"}
    return menu


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACT 1 cont. — Cart Management
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DELIVERY_FEE = 2.50


@_register("add_to_cart")
def add_to_cart(args: dict) -> dict:
    """Add a food item to the user's cart."""
    user_id = args.get("user_id", "")
    food_id = args.get("food_id", "")
    restaurant_id = args.get("restaurant_id", "")
    quantity = args.get("quantity", 1)
    special_requests = args.get("special_requests", "")

    # Find the food in our menu data
    menu = _MENUS.get(restaurant_id)
    if not menu:
        return {"error": f"Restaurant '{restaurant_id}' not found"}

    food = next((f for f in menu["items"] if f["id"] == food_id), None)
    if not food:
        return {"error": f"Food '{food_id}' not found in restaurant '{restaurant_id}'"}

    cart_item = {
        "food_id": food["id"],
        "name": food["name"],
        "price": food["price"],
        "quantity": quantity,
        "special_requests": special_requests,
        "restaurant_id": restaurant_id,
        "restaurant_name": menu["restaurant_name"],
        "image_url": food["image_url"],
    }

    if user_id not in _carts:
        _carts[user_id] = []
    _carts[user_id].append(cart_item)

    subtotal = sum(i["price"] * i["quantity"] for i in _carts[user_id])

    return {
        "added": cart_item,
        "cart_count": len(_carts[user_id]),
        "subtotal": subtotal,
        "delivery_fee": DELIVERY_FEE,
        "total": subtotal + DELIVERY_FEE,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACT 2 — Order & Payment
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@_register("get_order_summary")
def get_order_summary(args: dict) -> dict:
    """Return the current cart as an order summary."""
    user_id = args.get("user_id", "")
    cart = _carts.get(user_id, [])

    if not cart:
        return {"error": "Cart is empty"}

    subtotal = sum(i["price"] * i["quantity"] for i in cart)
    restaurant_name = cart[0]["restaurant_name"] if cart else ""

    return {
        "restaurant_name": restaurant_name,
        "items": [
            {
                "name": i["name"],
                "quantity": i["quantity"],
                "price": i["price"],
                "subtotal": i["price"] * i["quantity"],
                "special_requests": i["special_requests"],
            }
            for i in cart
        ],
        "subtotal": subtotal,
        "delivery_fee": DELIVERY_FEE,
        "total": subtotal + DELIVERY_FEE,
        "delivery_address": "Margaret's Home (saved address)",
        "estimated_delivery_min": 20,
        "payment_options": [
            {"key": "line_pay", "label": "💚 LINE Pay"},
            {"key": "cash", "label": "💵 Cash on Delivery"},
            {"key": "credit_card", "label": "💳 Credit Card"},
        ],
    }


@_register("place_order")
def place_order(args: dict) -> dict:
    """Confirm and place the order."""
    user_id = args.get("user_id", "")
    cart = _carts.get(user_id, [])

    if not cart:
        return {"error": "Cart is empty"}

    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    subtotal = sum(i["price"] * i["quantity"] for i in cart)
    restaurant_name = cart[0]["restaurant_name"]

    order = {
        "order_id": order_id,
        "user_id": user_id,
        "restaurant_name": restaurant_name,
        "items": [
            {
                "name": i["name"],
                "quantity": i["quantity"],
                "price": i["price"],
            }
            for i in cart
        ],
        "subtotal": subtotal,
        "delivery_fee": DELIVERY_FEE,
        "total": subtotal + DELIVERY_FEE,
        "delivery_address": "Margaret's Home (saved address)",
        "estimated_delivery_min": 20,
        "status": "pending_payment",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    _orders[order_id] = order
    _user_orders[user_id] = order_id

    return {
        "order_id": order_id,
        "status": "pending_payment",
        "total": order["total"],
        "payment_options": [
            {"key": "line_pay", "label": "💚 LINE Pay"},
            {"key": "cash", "label": "💵 Cash on Delivery"},
            {"key": "credit_card", "label": "💳 Credit Card"},
        ],
    }


@_register("initiate_payment")
def initiate_payment(args: dict) -> dict:
    """Initiate payment for an order."""
    user_id = args.get("user_id", "")
    order_id = args.get("order_id", "") or _user_orders.get(user_id, "")
    payment_method = args.get("payment_method", "line_pay")

    transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    order = _orders.get(order_id)

    if order:
        order["status"] = "awaiting_payment"
        order["payment_method"] = payment_method
        order["transaction_id"] = transaction_id
        amount = order["total"]
    else:
        if not order_id:
            order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        amount = 10.50

    return {
        "order_id": order_id,
        "transaction_id": transaction_id,
        "payment_method": payment_method,
        "amount": amount,
        "status": "awaiting_payment",
        "payment_url": f"https://pay.line.me/mock/{transaction_id}" if payment_method == "line_pay" else None,
    }


@_register("confirm_payment")
def confirm_payment(args: dict) -> dict:
    """Confirm that payment was successful."""
    user_id = args.get("user_id", "")
    order_id = args.get("order_id", "") or _user_orders.get(user_id, "")
    transaction_id = args.get("transaction_id", "")

    order = _orders.get(order_id)

    # Always clear cart on payment confirmation
    clear_user_state(user_id)

    if order:
        order["status"] = "confirmed"
        order["paid_at"] = datetime.now(timezone.utc).isoformat()
        amount = order["total"]
        payment_method = order.get("payment_method", "line_pay")
        restaurant_name = order["restaurant_name"]
        delivery_min = order["estimated_delivery_min"]
    else:
        if not order_id:
            order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        if not transaction_id:
            transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        amount = 10.50
        payment_method = "line_pay"
        restaurant_name = "Uncle Sam's Noodle House"
        delivery_min = 20

    return {
        "order_id": order_id,
        "transaction_id": transaction_id,
        "status": "confirmed",
        "amount_charged": amount,
        "payment_method": payment_method,
        "restaurant_name": restaurant_name,
        "estimated_delivery_min": delivery_min,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACT 3 — Order Tracking
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@_register("get_order_status")
def get_order_status(args: dict) -> dict:
    """Get the current status of an order."""
    user_id = args.get("user_id", "")
    order_id = args.get("order_id", "") or _user_orders.get(user_id, "")

    order = _orders.get(order_id)

    if order:
        status = order.get("status", "confirmed")
        restaurant_name = order["restaurant_name"]
        delivery_min = order["estimated_delivery_min"]
    else:
        if not order_id:
            order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        status = "confirmed"
        restaurant_name = "Uncle Sam's Noodle House"
        delivery_min = 20

    statuses_timeline = [
        {"status": "confirmed", "label": "Order Confirmed", "completed": True},
        {"status": "preparing", "label": "Restaurant Preparing", "completed": status in ("preparing", "rider_assigned", "picked_up", "on_the_way", "delivered")},
        {"status": "rider_assigned", "label": "Rider Assigned", "completed": status in ("rider_assigned", "picked_up", "on_the_way", "delivered")},
        {"status": "picked_up", "label": "Food Picked Up", "completed": status in ("picked_up", "on_the_way", "delivered")},
        {"status": "on_the_way", "label": "On The Way", "completed": status in ("on_the_way", "delivered")},
        {"status": "delivered", "label": "Delivered", "completed": status == "delivered"},
    ]

    return {
        "order_id": order_id,
        "status": status,
        "restaurant_name": restaurant_name,
        "estimated_delivery_min": delivery_min,
        "timeline": statuses_timeline,
        "rider": {
            "name": "James",
            "phone": "+66-XXX-XXX-1234",
            "vehicle": "Motorcycle",
        } if status in ("rider_assigned", "picked_up", "on_the_way") else None,
    }


@_register("track_rider")
def track_rider(args: dict) -> dict:
    """Get real-time rider location for an order."""
    user_id = args.get("user_id", "")
    order_id = args.get("order_id", "") or _user_orders.get(user_id, "")

    if not order_id:
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

    return {
        "order_id": order_id,
        "rider": {
            "name": "James",
            "phone": "+66-XXX-XXX-1234",
            "vehicle": "Motorcycle",
            "photo_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=100&h=100&fit=crop",
        },
        "location": {
            "lat": 13.7563,
            "lng": 100.5018,
            "heading": "Northwest",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        "destination": {
            "label": "Margaret's Home",
            "lat": 13.7580,
            "lng": 100.4990,
        },
        "estimated_arrival_min": 8,
        "distance_km": 1.2,
        "tracking_url": f"https://lineman.line.me/track/{order_id}",
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACT 4 — Review
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@_register("submit_review")
def submit_review(args: dict) -> dict:
    """Submit a review for a completed order."""
    user_id = args.get("user_id", "")
    order_id = args.get("order_id", "") or _user_orders.get(user_id, "")
    rating = args.get("rating", 5)
    tags = args.get("tags", [])
    comment = args.get("comment", "")

    if not order_id:
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

    order = _orders.get(order_id)
    restaurant_name = order["restaurant_name"] if order else "Uncle Sam's Noodle House"

    review_id = f"REV-{uuid.uuid4().hex[:8].upper()}"

    return {
        "review_id": review_id,
        "order_id": order_id,
        "restaurant_name": restaurant_name,
        "rating": rating,
        "tags": tags,
        "comment": comment,
        "status": "saved",
        "message": f"Thank you for your {rating}-star review!",
    }
