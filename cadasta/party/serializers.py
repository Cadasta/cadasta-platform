"""Party Serializers."""

from django.utils.translation import ugettext as _
from rest_framework import serializers

from .models import Party, PartyRelationship, TenureRelationship
from core import serializers as core_serializers
from spatial.serializers import SpatialUnitSerializer


class PartySerializer(core_serializers.JSONAttrsSerializer,
                      core_serializers.SanitizeFieldSerializer,
                      core_serializers.FieldSelectorSerializer,
                      serializers.ModelSerializer):
    attrs_selector = 'type'

    class Meta:
        model = Party
        fields = ('id', 'name', 'type', 'attributes', )
        read_only_fields = ('id', )

    def create(self, validated_data):
        project = self.context['project']
        return Party.objects.create(
            project=project, **validated_data)


class PartyRelationshipReadSerializer(serializers.ModelSerializer):

    party1 = PartySerializer(fields=('id', 'name', 'type'))
    party2 = PartySerializer(fields=('id', 'name', 'type'))
    rel_class = serializers.SerializerMethodField()

    class Meta:
        model = PartyRelationship
        fields = ('rel_class', 'id', 'party1', 'party2', 'type', 'attributes')
        read_only_fields = ('id',)

    def get_rel_class(self, obj):
        return 'party'


class PartyRelationshipWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = PartyRelationship
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
        return PartyRelationship.objects.create(
            project=project, **validated_data)


class TenureRelationshipReadSerializer(serializers.ModelSerializer):

    party = PartySerializer(fields=('id', 'name', 'type'))
    spatial_unit = SpatialUnitSerializer(fields=(
        'id', 'name', 'geometry', 'type'))
    rel_class = serializers.SerializerMethodField()

    class Meta:
        model = TenureRelationship
        fields = ('rel_class', 'id', 'party', 'spatial_unit', 'tenure_type',
                  'attributes')
        read_only_fields = ('id',)

    def get_rel_class(self, obj):
        return 'tenure'


class TenureRelationshipWriteSerializer(
        core_serializers.JSONAttrsSerializer,
        core_serializers.SanitizeFieldSerializer,
        serializers.ModelSerializer):

    class Meta:
        model = TenureRelationship
        fields = ('id', 'party', 'spatial_unit', 'tenure_type', 'attributes')
        read_only_fields = ('id',)

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
        return TenureRelationship.objects.create(
            project=project, **validated_data)
