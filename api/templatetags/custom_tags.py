"""Custom Django template filters for summary rendering."""

import math
import re
from decimal import Decimal

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
    if hasattr(value, str(arg)):
        return getattr(value, arg)
    if hasattr(value, "has_key") and value.has_key(arg):
        return value[arg]
    if numeric_test.match(str(arg)) and len(value) > int(arg):
        return value[int(arg)]
    return None


@register.filter(name="hasattr")
def hasattribute(value: object, arg: object) -> bool:
    """Return whether an object has the given attribute.

    Returns:
        True when the attribute exists on the value.
    """
    return hasattr(value, str(arg))


@register.filter
def iloc(items: object, index: object) -> object:
    """Return the item at the given index, or None on failure.

    Returns:
        The indexed item, or None when lookup fails.
    """
    try:
        return items[int(index)]  # type: ignore[index]
    except (IndexError, TypeError, ValueError):
        return None


@register.filter(name="zip")
def zip_lists(value: object, arg: object) -> zip[tuple[object, object]]:
    """Zip two iterables together.

    Returns:
        Zip object pairing items from both iterables.
    """
    return zip(value, arg, strict=False)  # type: ignore[arg-type]


@register.filter(name="range_inclu")
def make_range(value: object, arg: object) -> range:
    """Return an inclusive range from value through arg.

    Returns:
        Range spanning the requested values.
    """
    return range(int(value), int(arg) + 1)  # type: ignore[arg-type]


@register.filter
def add(value: object, arg: object) -> Decimal:
    """Add two decimal-compatible values.

    Returns:
        Sum of the operands as a Decimal.
    """
    return Decimal(value) + Decimal(arg)  # type: ignore[arg-type]


@register.filter
def sub(value: object, arg: object) -> Decimal:
    """Subtract arg from value.

    Returns:
        Difference of the operands as a Decimal.
    """
    return Decimal(value) - Decimal(arg)  # type: ignore[arg-type]


@register.filter
def multiply(value: object, arg: object) -> Decimal:
    """Multiply two decimal-compatible values.

    Returns:
        Product of the operands as a Decimal.
    """
    return Decimal(value) * Decimal(arg)  # type: ignore[arg-type]


@register.filter
def divide(value: object, arg: object) -> Decimal:
    """Divide value by arg.

    Returns:
        Quotient of the operands as a Decimal.
    """
    return Decimal(value) / Decimal(arg)  # type: ignore[arg-type]


@register.filter
def ceil(value: object) -> int:
    """Return the ceiling of a decimal-compatible value.

    Returns:
        Smallest integer greater than or equal to the value.
    """
    return math.ceil(Decimal(value))  # type: ignore[arg-type]


@register.filter
def floor(value: object) -> int:
    """Return the floor of a decimal-compatible value.

    Returns:
        Largest integer less than or equal to the value.
    """
    return math.floor(Decimal(value))  # type: ignore[arg-type]


@register.filter
def format_trace(value: object, arg: str) -> object:
    """Format trace precipitation or snowfall values for display.

    Returns:
        Formatted display value, trace label, or empty string.
    """
    try:
        if Decimal(value) == TRACE_VAL:  # type: ignore[arg-type]
            if arg == "dec":
                return 0.01
            if "str" in arg:
                return "Trace"
            return ""
        if "precip" in arg:
            return f"{Decimal(value):.2f}"  # type: ignore[arg-type]
        if "snow" in arg:
            return f"{Decimal(value):.1f}"  # type: ignore[arg-type]
        return Decimal(value)  # type: ignore[arg-type]

    except Exception as e:
        return str(e)


@register.filter
def format_dfn(value: object) -> str:
    """Format a departure-from-normal value with an explicit plus sign.

    Returns:
        String representation with a leading plus for positive values.
    """
    try:
        if float(value) > 0:  # type: ignore[arg-type]
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
    return map_dict[int(year)]  # type: ignore[arg-type]
