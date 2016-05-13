"""Party Serializers."""

from rest_framework import serializers

from core.serializers import DetailSerializer, FieldSelectorSerializer
from .models import Party


class PartySerializer(DetailSerializer,
                      FieldSelectorSerializer, serializers.ModelSerializer):

    class Meta:
        model = Party
        fields = ('id', 'name', 'type',
                  'contacts', 'attributes', 'project', 'relationships')
        read_only_fields = ('id',)
        detail_only_fields = []
