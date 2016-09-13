from django.db.models.query import QuerySet


class DetailSerializer:
    def __init__(self, *args, **kwargs):
        detail = kwargs.pop('detail', False)
        hide_detail = kwargs.pop('hide_detail', False)
        super(DetailSerializer, self).__init__(*args, **kwargs)

        is_list = type(self.instance) in [list, QuerySet]
        if hide_detail or (is_list and not detail):
            for field_name in self.Meta.detail_only_fields:
                self.fields.pop(field_name)


class FieldSelectorSerializer:
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super(FieldSelectorSerializer, self).__init__(*args, **kwargs)

        if fields:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)
