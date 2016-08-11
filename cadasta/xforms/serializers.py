from rest_framework import serializers
from core.serializers import FieldSelectorSerializer
from xforms.models import XFormSubmission
from accounts.models import User
from questionnaires.models import Questionnaire


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
        if obj.xml_form.url.startswith('/media/s3/uploads/'):
            if self.context['request'].META['SERVER_PROTOCOL'] == 'HTTP/1.1':
                url = 'http://'
            else:
                url = 'https://'
            url += self.context['request'].META.get('HTTP_HOST',
                                                    'localhost:8000')
            return url + obj.xml_form.url

        return obj.xml_form.url


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

    def create(self, validated_data):
        return XFormSubmission.objects.create(**validated_data)
