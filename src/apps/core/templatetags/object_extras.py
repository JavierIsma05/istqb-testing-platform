from django import template


register = template.Library()


@register.filter
def attr(obj, name):
    value = getattr(obj, name, '')
    if callable(value):
        return value()
    return value
