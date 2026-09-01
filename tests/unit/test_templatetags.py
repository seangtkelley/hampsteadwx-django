"""Unit tests for custom template filters."""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from api.templatetags.custom_tags import (
    add,
    ceil,
    divide,
    floor,
    format_dfn,
    format_trace,
    getattribute,
    hasattribute,
    iloc,
    make_range,
    map_snowseason_year,
    multiply,
    sub,
    zip_lists,
)
from boilerplate.settings import TRACE_VAL

pytestmark = pytest.mark.unit


def test_getattribute_attr_and_mapping_and_index() -> None:
    obj = SimpleNamespace(foo="bar")
    assert getattribute(obj, "foo") == "bar"
    assert getattribute({"a": 1}, "a") == 1
    assert getattribute(["x", "y"], "1") == "y"
    assert getattribute(obj, "missing") is None
    assert getattribute(["x"], "9") is None


def test_hasattribute() -> None:
    assert hasattribute(SimpleNamespace(a=1), "a") is True
    assert hasattribute(SimpleNamespace(a=1), "b") is False


def test_iloc() -> None:
    assert iloc(["a", "b", "c"], 1) == "b"
    assert iloc(["a"], 5) is None
    assert iloc(["a"], "nope") is None


def test_zip_lists() -> None:
    assert list(zip_lists([1, 2], ["a", "b"])) == [(1, "a"), (2, "b")]


def test_make_range() -> None:
    assert list(make_range(1, 3)) == [1, 2, 3]


def test_decimal_math_filters() -> None:
    assert add("1.5", "2.5") == Decimal("4.0")
    assert sub("5", "2") == Decimal("3")
    assert multiply("2", "3") == Decimal("6")
    assert divide("9", "2") == Decimal("4.5")
    assert ceil("2.1") == 3
    assert floor("2.9") == 2


def test_format_trace_variants() -> None:
    assert format_trace(TRACE_VAL, "dec") == pytest.approx(0.01)
    assert format_trace(TRACE_VAL, "str") == "Trace"
    assert format_trace(TRACE_VAL, "other") == ""
    assert format_trace("1.234", "precip") == "1.23"
    assert format_trace("1.26", "snow") == "1.3"
    assert format_trace("5", "plain") == Decimal("5")


def test_format_trace_error_returns_message() -> None:
    result = format_trace(object(), "precip")
    assert isinstance(result, str)
    assert result


def test_format_dfn() -> None:
    assert format_dfn("1.5") == "+1.5"
    assert format_dfn("-2.0") == "-2.0"
    assert format_dfn("0") == "0"
    assert isinstance(format_dfn(object()), str)


def test_map_snowseason_year() -> None:
    assert map_snowseason_year(2020, "2020-2021") == 1901
    assert map_snowseason_year(2021, "2020-2021") == 1902
    with pytest.raises(KeyError):
        map_snowseason_year(2019, "2020-2021")
