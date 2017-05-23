from django import template
from django.forms import ChoiceField, FileField, CharField


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
        field.field.widget.attrs['data-parsley-required'] = 'true'
    return field


@register.filter(name='set_parsley_sanitize')
def set_parsley_sanitize(field):
    if type(field.field) == CharField:
        field.field.widget.attrs['data-parsley-sanitize'] = '1'
    return field


@register.filter(name='format_area_metric_units')
def set_format_area_metric_units(area):
    formated_area = ''
    area = float(area)
    if area < 1000:
        formated_area = format(area, '.2f') + ' m<sup>2</sup>'
    else:
        ha = area/10000
        formated_area = format(ha, '.2f') + ' ha'
    return formated_area


@register.filter(name='format_area_imperial_units')
def set_format_area_imperial_units(area):
    formated_area = ''
    area = float(area)
    area_ft2 = area * 10.764
    if area_ft2 < 4356:
        formated_area = format(area_ft2, '.2f') + ' ft<sup>2</sup>'
    else:
        ac = area * 0.00024711
        formated_area = format(ac, '.2f') + ' ac'
    return formated_area
