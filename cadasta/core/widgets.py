from django.forms import Select, SelectMultiple
from jsonattrs.mixins import template_xlang_labels


class XLangSelect(Select):
    def __init__(self, xlang_labels, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xlang_labels = xlang_labels

    def render_option(self, selected_choices, option_value, option_label):
        rendered = super().render_option(
            selected_choices, option_value, option_label)
        rendered = rendered.replace(
            '<option',
            '<option ' + template_xlang_labels(
                self.xlang_labels.get(option_value, ''))
        )
        return rendered


class XLangSelectMultiple(XLangSelect, SelectMultiple):
    pass
