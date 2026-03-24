"""Tests for tool definitions."""

from shopping_agent.tools import TOOL_DEFINITIONS


def test_all_tools_have_required_fields():
    for tool in TOOL_DEFINITIONS:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool
        assert tool["input_schema"]["type"] == "object"


def test_tool_names_are_unique():
    names = [t["name"] for t in TOOL_DEFINITIONS]
    assert len(names) == len(set(names))


def test_expected_tools_exist():
    names = {t["name"] for t in TOOL_DEFINITIONS}
    expected = {
        "search_products",
        "get_product_details",
        "add_to_cart",
        "view_cart",
        "remove_from_cart",
        "checkout",
        "set_shipping_address",
        "confirm_order",
        "check_order_status",
    }
    assert expected.issubset(names)
