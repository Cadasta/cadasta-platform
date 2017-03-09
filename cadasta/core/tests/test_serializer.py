import pytest
from django.test import TestCase
from django.db import models

from jsonattrs.fields import JSONAttributeField
from rest_framework.serializers import ModelSerializer, ValidationError

from ..messages import SANITIZE_ERROR
from .. import serializers


class SerializerModel(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    number = models.IntegerField(null=True)
    attributes = JSONAttributeField(null=True, blank=True)

    class Meta:
        app_label = 'core'


class MyDetailSerializer(serializers.DetailSerializer, ModelSerializer):
    class Meta:
        model = SerializerModel
        fields = ('name', 'description',)
        detail_only_fields = ('description',)


class MyFieldSerializer(serializers.FieldSelectorSerializer, ModelSerializer):
    class Meta:
        model = SerializerModel
        fields = ('name', 'description',)


class MySanitizeFieldSerializer(serializers.SanitizeFieldSerializer,
                                ModelSerializer):
    class Meta:
        model = SerializerModel
        fields = ('name', 'description', 'number', 'attributes', )


class MyJSONAttrsSerializerSerializer(serializers.JSONAttrsSerializer,
                                      ModelSerializer):
    class Meta:
        model = SerializerModel
        fields = ('attributes', )


class DetailSerializerTest(TestCase):
    def test_detail_fields_are_included_with_single_instance(self):
        model = SerializerModel(
            name='Blah',
            description='Blah'
        )
        serializer = MyDetailSerializer(model)
        assert 'description' in serializer.data

    def test_detail_fields_are_not_included_when_instance_list(self):
        model = SerializerModel(
            name='Blah',
            description='Blah'
        )
        serializer = MyDetailSerializer([model], many=True)
        assert 'description' not in serializer.data[0]

    def test_detail_fields_are_included_when_instance_list_detail_true(self):
        model = SerializerModel(
            name='Blah',
            description='Blah'
        )
        serializer = MyDetailSerializer([model], detail=True, many=True)
        assert 'description' in serializer.data[0]

    def test_detail_fields_are_included_instance_is_created(self):
        data = {
            'name': 'Blah',
            'description': 'Blah'
        }
        serializer = MyDetailSerializer(data=data)
        assert serializer.is_valid()
        serializer.save()
        assert 'description' in serializer.data


class FieldSelectorSerializerTest(TestCase):
    def test_all_fields_are_included(self):
        model = SerializerModel(
            name='Blah',
            description='Blah'
        )
        serializer = MyFieldSerializer(model)
        assert 'name' in serializer.data
        assert 'description' in serializer.data

    def test_only_defined_fields_are_included(self):
        model = SerializerModel(
            name='Blah',
            description='Blah'
        )
        serializer = MyFieldSerializer(model, fields=('name',))
        assert 'name' in serializer.data
        assert 'description' not in serializer.data


class SanitizeFieldSerializerTest(TestCase):
    def test_valid(self):
        data = {
            'name': 'Name',
            'description': 'Description',
            'number': 2,
            'attributes': {'key': 'value'}
        }
        serializer = MySanitizeFieldSerializer(data=data)
        assert serializer.validate(data) == data

    def test_trim_whitespace(self):
        data = {
            'name': '   Name    ',
            'number': 2
        }
        serializer = MySanitizeFieldSerializer(data=data)
        assert serializer.validate(data)['name'] == 'Name'

    def test_trim_tabs(self):
        data = {
            'name': '	Name	',
            'number': 2
        }
        serializer = MySanitizeFieldSerializer(data=data)
        assert serializer.validate(data)['name'] == 'Name'

    def test_invalid(self):
        data = {
            'name': '<Name>',
            'description': '<Description>',
            'number': 2,
            'attributes': {'key': '<value>'}
        }
        serializer = MySanitizeFieldSerializer(data=data)
        with pytest.raises(ValidationError) as e:
            serializer.validate(data)
        assert SANITIZE_ERROR in e.value.detail['name']
        assert SANITIZE_ERROR in e.value.detail['description']
        assert SANITIZE_ERROR in e.value.detail['attributes']
