from django import template

register = template.Library()


@register.simple_tag
def wizard_step_classes(step, tag):
    classes = []
    if step == tag:
        classes.append('active')
    if step >= tag:
        classes.append('enabled')
    if step > tag:
        classes.append('complete')
    return ' '.join(classes)
