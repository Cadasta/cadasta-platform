from collections import OrderedDict
from core.mixins import SchemaSelectorMixin
from django.contrib.contenttypes.models import ContentType


class Exporter(SchemaSelectorMixin):
    def __init__(self, project):
        self.project = project
        self._schema_attrs = {}

    def get_schema_attrs(self, content_type):
        label = '{0}.{1}'.format(content_type.app_label, content_type.model)
        if self._schema_attrs == {}:
            self._schema_attrs = self.get_attributes(self.project)
        return self._schema_attrs[label]

    def get_values(self, item, model_attrs, schema_attrs):
        values = OrderedDict()
        for attr in model_attrs:
            if '.' in attr:
                attr_items = attr.split('.')
                value = None
                for a in attr_items:
                    value = (getattr(item, a)
                             if not value else getattr(value, a))
                values[attr] = value
            else:
                values[attr] = getattr(item, attr)

        content_type = ContentType.objects.get_for_model(item)
        conditional_selector = self.get_conditional_selector(content_type)
        if conditional_selector:
            entity_type = getattr(item, conditional_selector)
            attributes = schema_attrs.get(entity_type, {})
        else:
            attributes = schema_attrs.get('DEFAULT', {})
        for key, attr in attributes.items():
            attr_value = item.attributes.get(key, '')
            if type(attr_value) == list:
                attr_value = (', ').join(attr_value)
            values[key] = attr_value

        return values
