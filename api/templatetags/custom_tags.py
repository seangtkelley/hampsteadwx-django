import re
from decimal import *
import math

from django import template

register = template.Library()

numeric_test = re.compile(r"^\d+$")

@register.filter(name='getattr')
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

@register.filter(name='hasattr')
def hasattribute(value, arg):
    return hasattr(value, str(arg))

@register.filter
def iloc(l, i):
    try:
        return l[int(i)]
    except:
        return None

@register.filter(name='zip')
def zip_lists(value, arg):
    return zip(value, arg)

@register.filter(name='range_inclu')
def make_range(value, arg):
    return range(int(value), int(arg)+1)

@register.filter
def add(value, arg):
    return Decimal(value) + Decimal(arg)

@register.filter
def sub(value, arg):
    return Decimal(value) - Decimal(arg)

@register.filter
def multiply(value, arg):
    return Decimal(value) * Decimal(arg)

@register.filter
def divide(value, arg):
    return Decimal(value) / Decimal(arg)

@register.filter
def ceil(value):
    return math.ceil(Decimal(value))

@register.filter
def floor(value):
    return math.floor(Decimal(value))


@register.filter
def format_trace(value, arg):
    try:
        if float(value) == 0.001:
            if arg == 'dec':
                # for graphs
                return 0.01
            elif 'str' in arg:
                return "Trace"
            else:
                return ""
        else:
            if 'precip' in arg:
                return f"{Decimal(value):.2f}"
            elif 'snow' in arg:
                return f"{Decimal(value):.1f}"
            else:
                return Decimal(value)
                
    except Exception as e:
        return str(e)
    
@register.filter
def format_dfn(value):
    if float(value) > 0:
        return '+' + str(value)
    else:
        return str(value)