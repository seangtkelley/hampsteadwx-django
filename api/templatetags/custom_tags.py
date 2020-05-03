import re
from django import template

register = template.Library()

numeric_test = re.compile(r"^\d+$")

@register.filter
def getattribute(value, arg):
    """Gets an attribute of an object dynamically from a string name"""

    if hasattr(value, str(arg)):
        return getattr(value, arg)
    elif hasattr(value, 'has_key') and value.has_key(arg):
        return value[arg]
    elif numeric_test.match(str(arg)) and len(value) > int(arg):
        return value[int(arg)]
    else:
        return None

@register.filter(name='zip')
def zip_lists(value, arg):
    return zip(value, arg)


@register.filter
def multiply(value, arg):
    return value * arg


@register.filter
def format_trace(value, arg):
    if int(value) == -77:
        if arg == 'dec':
            # for graphs
            return 0.01
        elif arg == 'str':
            return "Trace"
        else:
            return ""
    else:
        return Decimal(value)
