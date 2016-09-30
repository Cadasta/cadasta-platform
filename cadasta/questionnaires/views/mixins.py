from jsonattrs.mixins import JsonAttrsMixin
from ..functions import select_multilang_field_label


class JsonAttrsMultiLangMixin(JsonAttrsMixin):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        attrs = context[self.attributes_field]
        context[self.attributes_field] = [
            (select_multilang_field_label(a[0]), a[1]) for a in attrs
        ]
        return context
