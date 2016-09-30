from jsonattrs.forms import AttributeModelForm
from .functions import select_multilang_field_label


class AttributeMultiLangModelForm(AttributeModelForm):
    def add_attribute_fields(self, schema_selectors):
        """For each field label of the form, this method runs the
        select_multilang_field_label() function to get the correct label."""
        super().add_attribute_fields(schema_selectors)
        for key, field in self.fields.items():
            if field.label:
                field.label = select_multilang_field_label(field.label)
