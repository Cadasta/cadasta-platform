from django.test import TestCase
from django.db import models
from rest_framework.serializers import ModelSerializer

from ..serializers import DetailSerializer, FieldSelectorSerializer


class SerializerModel(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)

    class Meta:
        app_label = 'core'


class MyDetailSerializer(DetailSerializer, ModelSerializer):
    class Meta:
        model = SerializerModel
        fields = ('name', 'description',)
        detail_only_fields = ('description',)


class MyFieldSerializer(FieldSelectorSerializer, ModelSerializer):
    class Meta:
        model = SerializerModel
        fields = ('name', 'description',)


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
