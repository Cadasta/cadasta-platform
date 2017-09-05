from django import template
register = template.Library()


@register.assignment_tag
def define(value=None):
    return value
