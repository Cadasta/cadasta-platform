from rest_framework import serializers
from rest_framework_gis import serializers as geo_serializers

from core.serializers import DetailSerializer, FieldSelectorSerializer
from organization.serializers import OrganizationSerializer

from .models import SpatialUnit
from organization.models import Project


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


class SpatialUnitSerializer(DetailSerializer,
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
        return SpatialUnit.objects.create(project_id=project.id,
                                          **validated_data)
