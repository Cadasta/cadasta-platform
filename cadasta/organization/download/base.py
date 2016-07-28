from jsonattrs.models import Schema


class Exporter():
    def __init__(self, project):
        self.project = project
        self._schema_attrs = {}

    def get_schema_attrs(self, content_type):
        content_type_key = '{}.{}'.format(content_type.app_label,
                                          content_type.model)

        if content_type_key not in self._schema_attrs.keys():
            selectors = [
                self.project.organization.id,
                self.project.id,
                self.project.current_questionnaire
            ]
            schemas = Schema.objects.lookup(
                content_type=content_type, selectors=selectors
            )

            attrs = []
            if schemas:
                attrs = [
                    a for s in schemas
                    for a in s.attributes.all() if not a.omit
                ]
            self._schema_attrs[content_type_key] = attrs

        return self._schema_attrs[content_type_key]

    def get_values(self, item, model_attrs, schema_attrs):
        values = []
        for attr in model_attrs:
            if '.' in attr:
                attr_items = attr.split('.')
                value = None
                for a in attr_items:
                    value = (getattr(item, a)
                             if not value else getattr(value, a))
                values.append(value)
            else:
                values.append(getattr(item, attr))

        for attr in schema_attrs:
            values.append(item.attributes.get(attr.name, ''))

        return values
