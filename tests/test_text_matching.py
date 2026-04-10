"""Tests for text matching utilities."""

from app.utils.text_matching import is_greeting, fuzzy_match


class TestIsGreeting:
    def test_exact_hello(self):
        assert is_greeting("hello") is True

    def test_exact_hi(self):
        assert is_greeting("hi") is True

    def test_case_insensitive(self):
        assert is_greeting("Hello") is True
        assert is_greeting("HELLO") is True

    def test_with_whitespace(self):
        assert is_greeting("  hello  ") is True

    def test_hello_in_sentence(self):
        assert is_greeting("hello there") is True

    def test_order_keyword(self):
        assert is_greeting("order") is True

    def test_menu_keyword(self):
        assert is_greeting("menu") is True

    def test_not_greeting(self):
        assert is_greeting("noodles") is False
        assert is_greeting("I want pizza") is False

    def test_empty(self):
        assert is_greeting("") is False


class TestFuzzyMatch:
    def test_exact_match(self):
        options = ["Noodles", "Rice", "Pizza"]
        assert fuzzy_match("Noodles", options) == "Noodles"

    def test_case_insensitive(self):
        options = ["Noodles", "Rice", "Pizza"]
        assert fuzzy_match("noodles", options) == "Noodles"

    def test_partial_match(self):
        options = ["Uncle Sam's Noodle House", "Mama Chen's"]
        assert fuzzy_match("Uncle Sam", options) == "Uncle Sam's Noodle House"

    def test_no_match(self):
        options = ["Noodles", "Rice"]
        assert fuzzy_match("burger", options) is None

    def test_with_emoji(self):
        options = ["\U0001f49a LINE Pay", "\U0001f4b5 Cash on Delivery"]
        assert fuzzy_match("LINE Pay", options) == "\U0001f49a LINE Pay"

    def test_empty_text(self):
        options = ["A", "B"]
        assert fuzzy_match("", options) is None
