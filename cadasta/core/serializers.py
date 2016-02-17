from django.db.models.query import QuerySet


class DetailSerializer:
    def __init__(self, *args, **kwargs):
        detail = kwargs.pop('detail', False)
        super(DetailSerializer, self).__init__(*args, **kwargs)

        is_list = type(self.instance) in [list, QuerySet]
        if is_list and not detail:
            for field_name in self.Meta.detail_only_fields:
                self.fields.pop(field_name)
