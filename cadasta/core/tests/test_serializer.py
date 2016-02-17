from django.test import TestCase
from django.db import models
from rest_framework.serializers import ModelSerializer

from ..serializers import DetailSerializer


class SerializerModel(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)

    class Meta:
        app_label = 'core'


class MyTestSerializer(DetailSerializer, ModelSerializer):
    class Meta:
        model = SerializerModel
        fields = ('name', 'description',)
        detail_only_fields = ('description',)


class DetailSerializerTest(TestCase):
    def test_detail_fields_are_included_with_single_instance(self):
        model = SerializerModel(
            name='Blah',
            description='Blah'
        )
        serializer = MyTestSerializer(model)
        assert 'description' in serializer.data

    def test_detail_fields_are_not_included_when_instance_list(self):
        model = SerializerModel(
            name='Blah',
            description='Blah'
        )
        serializer = MyTestSerializer([model], many=True)
        assert 'description' not in serializer.data[0]

    def test_detail_fields_are_included_when_instance_list_detail_true(self):
        model = SerializerModel(
            name='Blah',
            description='Blah'
        )
        serializer = MyTestSerializer([model], detail=True, many=True)
        assert 'description' in serializer.data[0]

    def test_detail_fields_are_included_instance_is_created(self):
        data = {
            'name': 'Blah',
            'description': 'Blah'
        }
        serializer = MyTestSerializer(data=data)
        assert serializer.is_valid()
        serializer.save()
        assert 'description' in serializer.data
