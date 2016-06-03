from .models import Resource, ContentObject
from rest_framework import serializers
from django.utils.translation import ugettext as _

from buckets.serializers import S3Field


class ResourceSerializer(serializers.ModelSerializer):
    file = S3Field()

    class Meta:
        model = Resource
        fields = ('id', 'name', 'description', 'file', 'original_file',
                  'archived',)
        read_only_fields = ('id', )

    def is_valid(self, raise_exception=False):
        data = self.initial_data
        if 'id' in data:
            try:
                self.resource = Resource.objects.get(id=data['id'])
                self._errors = {}
                self._validated_data = data
                return True
            except Resource.DoesNotExist:
                self._errors = {'id': _('Resource not found')}
                if raise_exception:
                    raise serializers.ValidationError(self._errors)
                return False

        return super().is_valid(raise_exception=raise_exception)

    def create(self, validated_data):
        if 'id' in validated_data:
            ContentObject.objects.create(
                resource_id=validated_data['id'],
                content_object=self.context['content_object']
            )
            return self.resource
        else:
            return Resource.objects.create(
                content_object=self.context['content_object'],
                contributor=self.context['contributor'],
                project_id=self.context['project_id'],
                **validated_data
            )
