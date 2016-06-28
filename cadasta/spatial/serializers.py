from django.utils.translation import ugettext as _
from rest_framework import serializers
from rest_framework_gis import serializers as geo_serializers

from .models import SpatialUnit, SpatialRelationship
from organization.models import Project
from core.serializers import DetailSerializer, FieldSelectorSerializer
from organization.serializers import OrganizationSerializer


class ProjectSpatialUnitSerializer(DetailSerializer, FieldSelectorSerializer,
                                   serializers.ModelSerializer):
    organization = OrganizationSerializer(
        read_only=True, fields=('id', 'name', 'slug')
    )

    class Meta:
        model = Project
        fields = ('id', 'organization', 'name', 'slug')
        read_only_fields = ('id', 'slug')
        detail_only_fields = ('organization',)


class SpatialUnitSerializer(DetailSerializer, FieldSelectorSerializer,
                            geo_serializers.GeoFeatureModelSerializer):
    project = ProjectSpatialUnitSerializer(read_only=True)

    class Meta:
        model = SpatialUnit
        context_key = 'project'
        geo_field = 'geometry'
        id_field = False
        fields = ('id', 'name',
                  'geometry', 'type', 'attributes',
                  'relationships', 'project',)
        read_only_fields = ('id', 'project',)
        detail_only_fields = ('project',)

    def create(self, validated_data):
        project = self.context['project']
        return SpatialUnit.objects.create(
            project_id=project.id, **validated_data)


class SpatialRelationshipReadSerializer(serializers.ModelSerializer):

    su1 = SpatialUnitSerializer(fields=('id', 'name', 'geometry', 'type'))
    su2 = SpatialUnitSerializer(fields=('id', 'name', 'geometry', 'type'))
    rel_class = serializers.SerializerMethodField()

    class Meta:
        model = SpatialRelationship
        fields = ('rel_class', 'id', 'su1', 'su2', 'type', 'attributes')
        read_only_fields = ('id',)

    def get_rel_class(self, obj):
        return 'spatial'


class SpatialRelationshipWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = SpatialRelationship
        fields = ('id', 'su1', 'su2', 'type', 'attributes')
        read_only_fields = ('id',)

    def validate(self, data):
        if self.instance:
            su1 = data.get('su1', self.instance.su1)
            su2 = data.get('su2', self.instance.su2)
        else:
            su1 = data['su1']
            su2 = data['su2']
        if su1.id == su2.id:
            raise serializers.ValidationError(
                _("The spatial units must be different"))
        elif su1.project.slug != su2.project.slug:
            err_msg = _(
                "'su1' project ({}) should be equal to 'su2' project ({})")
            raise serializers.ValidationError(
                err_msg.format(su1.project.slug, su2.project.slug))
        return data

    def create(self, validated_data):
        project = self.context['project']
        return SpatialRelationship.objects.create(
            project=project, **validated_data)
