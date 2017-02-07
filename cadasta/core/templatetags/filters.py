from django import template
from django.forms import ChoiceField, FileField

register = template.Library()


@register.filter(name='field_value')
def field_value(field):
    """Return the value for this BoundField."""
    if field.form.is_bound:
        if isinstance(field.field, FileField) and field.data is None:
            val = field.form.initial.get(field.name, field.field.initial)
        else:
            val = field.data
    else:
        val = field.form.initial.get(field.name, field.field.initial)
        if callable(val):
            val = val()
    if val is None:
        val = ''
    return val


@register.filter(name='display_choice_verbose')
def display_choice_verbose(field):
    """Return the displayed value for this BoundField."""
    if isinstance(field.field, ChoiceField):
        value = field_value(field)
        for (val, desc) in field.field.choices:
            if val == value:
                return desc


@register.filter(name='set_parsley_required')
def set_parsley_required(field):
    if field.field.required:
        field.field.widget.attrs = {
            'data-parsley-required': 'true'
        }
    return field
