"""Custom Django template filters for summary rendering."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal
from typing import Any, cast

from django import template

from boilerplate.settings import TRACE_VAL

register = template.Library()

numeric_test = re.compile(r"^\d+$")


@register.filter(name="getattr")
def getattribute(value: object, arg: object) -> object:
    """Get an attribute of an object dynamically from a string name.

    Args:
        value: Object or mapping to read from.
        arg: Attribute name, key, or numeric index.

    Returns:
        The resolved attribute value, or None if not found.
    """
    name = str(arg)
    if hasattr(value, name):
        return getattr(value, name)
    if isinstance(value, Mapping) and arg in value:
        value = cast(Mapping[Any, Any], value)
        return value[arg]
    # Sequence but not text
    if (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and numeric_test.match(name)
    ):
        idx = int(name)
        seq = cast(Sequence[Any], value)
        if -len(seq) <= idx < len(seq):
            return seq[idx]
    return None


@register.filter(name="hasattr")
def hasattribute(value: object, arg: object) -> bool:
    """Return whether an object has the given attribute.

    Returns:
        True when the attribute exists on the value.
    """
    return hasattr(value, str(arg))


@register.filter
def iloc(items: Iterable[Any] | Sequence[Any], index: object) -> object:
    """Return the item at the given index, or None on failure.

    Returns:
        The indexed item, or None when lookup fails.
    """
    try:
        return cast(Sequence[Any], items)[int(str(index))]
    except (IndexError, TypeError, ValueError):
        return None


@register.filter(name="zip")
def zip_lists(value: object, arg: object) -> zip[tuple[object, object]]:
    """Zip two iterables together.

    Returns:
        Zip object pairing items from both iterables.
    """
    return zip(cast(Iterable[Any], value), cast(Iterable[Any], arg), strict=False)


@register.filter(name="range_inclu")
def make_range(value: object, arg: object) -> range:
    """Return an inclusive range from value through arg.

    Returns:
        Range spanning the requested values.
    """
    return range(int(str(value)), int(str(arg)) + 1)


@register.filter
def add(value: object, arg: object) -> Decimal:
    """Add two decimal-compatible values.

    Returns:
        Sum of the operands as a Decimal.
    """
    return Decimal(str(value)) + Decimal(str(arg))


@register.filter
def sub(value: object, arg: object) -> Decimal:
    """Subtract arg from value.

    Returns:
        Difference of the operands as a Decimal.
    """
    return Decimal(str(value)) - Decimal(str(arg))


@register.filter
def multiply(value: object, arg: object) -> Decimal:
    """Multiply two decimal-compatible values.

    Returns:
        Product of the operands as a Decimal.
    """
    return Decimal(str(value)) * Decimal(str(arg))


@register.filter
def divide(value: object, arg: object) -> Decimal:
    """Divide value by arg.

    Returns:
        Quotient of the operands as a Decimal.
    """
    return Decimal(str(value)) / Decimal(str(arg))


@register.filter
def ceil(value: object) -> int:
    """Return the ceiling of a decimal-compatible value.

    Returns:
        Smallest integer greater than or equal to the value.
    """
    return math.ceil(Decimal(str(value)))


@register.filter
def floor(value: object) -> int:
    """Return the floor of a decimal-compatible value.

    Returns:
        Largest integer less than or equal to the value.
    """
    return math.floor(Decimal(str(value)))


@register.filter
def format_trace(value: object, arg: str) -> object:
    """Format trace precipitation or snowfall values for display.

    Returns:
        Formatted display value, trace label, or empty string.
    """
    try:
        if Decimal(str(value)) == TRACE_VAL:
            if arg == "dec":
                return 0.01  # for graphs
            if "str" in arg:
                return "Trace"
            return ""
        if "precip" in arg:
            return f"{Decimal(str(value)):.2f}"
        if "snow" in arg:
            return f"{Decimal(str(value)):.1f}"
        return Decimal(str(value))

    except Exception as e:
        return str(e)


@register.filter
def format_dfn(value: object) -> str:
    """Format a departure-from-normal value with an explicit plus sign.

    Returns:
        String representation with a leading plus for positive values.
    """
    try:
        if float(str(value)) > 0:
            return "+" + str(value)
        return str(value)
    except Exception as e:
        return str(e)


@register.filter
def map_snowseason_year(year: object, season: str) -> int:
    """Map a calendar year to a snow-season chart axis label.

    Returns:
        Chart axis year for the requested season component.
    """
    map_dict = {int(season.split("-")[0]): 1901, int(season.split("-")[1]): 1902}
    return map_dict[int(str(year))]
