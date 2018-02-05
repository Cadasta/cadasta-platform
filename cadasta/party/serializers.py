"""Party Serializers."""

from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from rest_framework import serializers

from core import serializers as core_serializers
from core.form_mixins import get_types
from spatial.serializers import SpatialUnitSerializer
from questionnaires.models import QuestionOption
from . import models
from .choices import TENURE_RELATIONSHIP_TYPES


class PartySerializer(core_serializers.JSONAttrsSerializer,
                      core_serializers.SanitizeFieldSerializer,
                      core_serializers.FieldSelectorSerializer,
                      serializers.ModelSerializer):
    attrs_selector = 'type'
    type_display = serializers.SerializerMethodField()

    class Meta:
        model = models.Party
        fields = ('id', 'name', 'type', 'attributes', 'type_display')
        read_only_fields = ('id', )

    @cached_property
    def type_displays_translations(self):
        project = self.context['project']
        return dict(QuestionOption.objects.filter(
            question__name='party_type',
            question__questionnaire_id=project.current_questionnaire
        ).values_list('name', 'label_xlat'))

    def get_type_display(self, instance):
        return self.type_displays_translations.get(instance.type,
                                                   instance.get_type_display())

    def create(self, validated_data):
        project = self.context['project']
        return models.Party.objects.create(
            project=project, **validated_data)


class PartyRelationshipSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.PartyRelationship
        fields = ('id', 'party1', 'party2', 'type', 'attributes')
        read_only_fields = ('id',)

    def validate(self, data):
        if self.instance:
            party1 = data.get('party1', self.instance.party1)
            party2 = data.get('party2', self.instance.party2)
        else:
            party1 = data['party1']
            party2 = data['party2']
        if party1.id == party2.id:
            raise serializers.ValidationError(
                _("The parties must be different"))
        elif party1.project.slug != party2.project.slug:
            err_msg = _(
                "'party1' project ({}) should be equal to"
                " 'party2' project ({})")
            raise serializers.ValidationError(
                err_msg.format(party1.project.slug, party2.project.slug))
        return data

    def create(self, validated_data):
        project = self.context['project']
        return models.PartyRelationship.objects.create(
            project=project, **validated_data)


class PartyRelationshipDetailSerializer(serializers.ModelSerializer):

    party1 = PartySerializer(fields=('id', 'name', 'type'))
    party2 = PartySerializer(fields=('id', 'name', 'type'))
    rel_class = serializers.SerializerMethodField()

    class Meta:
        model = models.PartyRelationship
        fields = ('rel_class', 'id', 'party1', 'party2', 'type', 'attributes')
        read_only_fields = ('id',)

    def get_rel_class(self, obj):
        return 'party'


class TenureRelationshipSerializer(
        core_serializers.JSONAttrsSerializer,
        core_serializers.SanitizeFieldSerializer,
        serializers.ModelSerializer):

    class Meta:
        model = models.TenureRelationship
        fields = ('id', 'party', 'spatial_unit', 'tenure_type', 'attributes')
        read_only_fields = ('id',)

    def validate_tenure_type(self, value):
        prj = self.context['project']
        allowed_types = get_types('tenure_type',
                                  TENURE_RELATIONSHIP_TYPES,
                                  questionnaire_id=prj.current_questionnaire)

        if value not in allowed_types:
            msg = "'{}' is not a valid choice for field 'tenure_type'."
            raise serializers.ValidationError(msg.format(value))

        return value

    def validate(self, data):
        data = super().validate(data)

        if self.instance:
            party = data.get('party', self.instance.party)
            spatial_unit = data.get('spatial_unit', self.instance.spatial_unit)
        else:
            party = data['party']
            spatial_unit = data['spatial_unit']
        if party.project.slug != spatial_unit.project.slug:
            err_msg = _(
                "'party' project ({}) should be equal to"
                " 'spatial_unit' project ({})")
            raise serializers.ValidationError(
                err_msg.format(party.project.slug, spatial_unit.project.slug))
        return data

    def create(self, validated_data):
        project = self.context['project']
        return models.TenureRelationship.objects.create(
            project=project, **validated_data)


class TenureRelationshipDetailSerializer(serializers.ModelSerializer):

    party = PartySerializer(fields=('id', 'name', 'type'))
    spatial_unit = SpatialUnitSerializer(fields=(
        'id', 'name', 'geometry', 'type'))
    rel_class = serializers.SerializerMethodField()

    class Meta:
        model = models.TenureRelationship
        fields = ('rel_class', 'id', 'party', 'spatial_unit', 'tenure_type',
                  'attributes')
        read_only_fields = ('id',)

    def get_rel_class(self, obj):
        return 'tenure'
