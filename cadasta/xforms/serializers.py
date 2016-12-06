from django.core.urlresolvers import reverse
from rest_framework import serializers
from core.serializers import FieldSelectorSerializer
from xforms.models import XFormSubmission
from accounts.models import User
from questionnaires.models import Questionnaire
from spatial.serializers import SpatialUnitSerializer
from party import serializers as party_serializer


class XFormListSerializer(FieldSelectorSerializer,
                          serializers.Serializer):
    """
    Serves up the /collect/formList/ api requests
    Returns back valid xml for xforms
    """
    formID = serializers.CharField(source='id_string')
    name = serializers.CharField(source='title')
    version = serializers.IntegerField()
    hash = serializers.CharField(source='md5_hash')
    downloadUrl = serializers.SerializerMethodField('get_xml_form')

    def get_xml_form(self, obj):
        url = reverse('form-download', args=[obj.id])
        url = self.context['request'].build_absolute_uri(url)
        if self.context['request'].META['SERVER_PROTOCOL'] == 'HTTPS/1.1':
            url = url.replace('http://', 'https://')
        return url


class XFormSubmissionSerializer(FieldSelectorSerializer,
                                serializers.Serializer):
    """
    Saves the full xml response from GeoODK Collect as a json object.
    """

    json_submission = serializers.JSONField(required=False)
    user = serializers.PrimaryKeyRelatedField(
        allow_null=True, queryset=User.objects.all(), required=False)
    questionnaire = serializers.PrimaryKeyRelatedField(
        allow_null=True, queryset=Questionnaire.objects.all(), required=False)
    instanceID = serializers.UUIDField(format='hex_verbose')

    parties = party_serializer.PartySerializer(read_only=True, many=True)
    spatial_units = SpatialUnitSerializer(read_only=True, many=True)
    tenure_relationships = party_serializer.TenureRelationshipReadSerializer(
        read_only=True, many=True)

    def create(self, validated_data):
        return XFormSubmission.objects.create(**validated_data)
