from django.db.models.query import QuerySet
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from core.mixins import SchemaSelectorMixin
from core.validators import sanitize_string
from core.messages import SANITIZE_ERROR
from rest_framework import serializers


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


class SanitizeFieldSerializer:
    def validate(self, data):
        data = super().validate(data)

        errors = {}

        for name, field in self.fields.items():
            if type(field) is serializers.CharField:
                value = data.get(name)
                if value:
                    value = value.strip()
                    data[name] = value
                valid = sanitize_string(value)
            elif type(field) is serializers.JSONField:
                value = data.get(name, {}) or {}
                valid = all(sanitize_string(value[k]) for k in value)

            if not valid:
                errors[name] = [SANITIZE_ERROR]

        if errors:
            raise serializers.ValidationError(errors)

        return data


class JSONAttrsSerializer(SchemaSelectorMixin):
    def validate_attributes(self, attrs):
        errors = []
        content_type = ContentType.objects.get_for_model(self.Meta.model)
        label = '{}.{}'.format(content_type.app_label, content_type.model)

        attrs_selector = 'DEFAULT'
        if hasattr(self, 'attrs_selector'):
            attrs_selector = self.initial_data[self.attrs_selector]

        attributes = self.get_model_attributes(self.context['project'], label)
        attributes = attributes.get(attrs_selector, {})

        for key, value in attrs.items():
            try:
                attr = attributes[key]
            except KeyError:
                errors += 'Unknown key "{}"'.format(key)
            else:
                try:
                    attr.validate(value)
                except ValidationError as e:
                    errors += e.messages
                else:
                    if hasattr(value, 'strip'):
                        attrs[key] = value.strip()

        if errors:
            raise serializers.ValidationError(errors)

        return attrs
