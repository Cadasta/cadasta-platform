from collections import namedtuple

from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from rest_framework import serializers
from rest_framework_gis import serializers as geo_serializers

from .models import SpatialUnit, SpatialRelationship
from core import serializers as core_serializers
from core.form_mixins import get_types
from .choices import TYPE_CHOICES


class SpatialUnitSerializer(core_serializers.JSONAttrsSerializer,
                            core_serializers.SanitizeFieldSerializer,
                            core_serializers.FieldSelectorSerializer,
                            geo_serializers.GeoFeatureModelSerializer):

    class Meta:
        model = SpatialUnit
        context_key = 'project'
        geo_field = 'geometry'
        id_field = False
        fields = ('id', 'geometry', 'type', 'attributes', 'area',)
        read_only_fields = ('id', )

    def validate_type(self, value):
        prj = self.context['project']
        allowed_types = get_types('location_type',
                                  TYPE_CHOICES,
                                  questionnaire_id=prj.current_questionnaire)

        if value not in allowed_types:
            msg = "'{}' is not a valid choice for field 'type'."
            raise serializers.ValidationError(msg.format(value))

        return value

    def create(self, validated_data):
        project = self.context['project']
        return SpatialUnit.objects.create(
            project_id=project.id, **validated_data)


class SpatialUnitGeoJsonSerializer(geo_serializers.GeoFeatureModelSerializer):
    url = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    fixed_precision_geometry = geo_serializers.GeometrySerializerMethodField()

    class Meta:
        model = SpatialUnit
        geo_field = 'fixed_precision_geometry'
        fields = ('id', 'type', 'url')

    def get_fixed_precision_geometry(self, location):
        """ Field to return geometry rounded down to a specified precision """
        if not location.geometry:
            return None
        # Notes on precision notes:
        # https://gis.stackexchange.com/questions/8650/measuring-accuracy-of-latitude-and-longitude/8674#8674  # NOQA
        # - The fourth decimal place is worth up to 11 m: it can identify a
        #   parcel of land. It is comparable to the typical accuracy of an
        #   uncorrected GPS unit with no interference.
        # - The fifth decimal place is worth up to 1.1 m: it distinguish trees
        #   from each other. Accuracy to this level with commercial GPS units
        #   can only be achieved with differential correction.
        # - The sixth decimal place is worth up to 0.11 m: you can use this for
        #   laying out structures in detail, for designing landscapes, building
        #   roads. It should be more than good enough for tracking movements of
        #   glaciers and rivers. This can be achieved by taking painstaking
        #   measures with GPS, such as differentially corrected GPS.
        precision = 5

        features = []
        for feature in location.geometry.coords:
            coords = []
            for f_coords in feature:
                # Decrease precision
                r_coords = tuple(round(coord, precision) for coord in f_coords)

                # Rm duplicates
                if coords and coords[-1] == r_coords:
                    continue
                coords.append(r_coords)
            features.append(coords)

        Feature = namedtuple('Feature', 'geom_type,coords')
        return Feature(location.geometry.geom_type, tuple(features))

    def get_url(self, location):
        project = location.project
        return reverse(
            'locations:detail',
            kwargs={'organization': project.organization.slug,
                    'project': project.slug,
                    'location': location.id})

    def get_type(self, location):
        return location.name


class SpatialRelationshipSerializer(serializers.ModelSerializer):

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


class SpatialRelationshipDetailSerializer(serializers.ModelSerializer):

    su1 = SpatialUnitSerializer(fields=('id', 'geometry', 'type'))
    su2 = SpatialUnitSerializer(fields=('id', 'geometry', 'type'))
    rel_class = serializers.SerializerMethodField()

    class Meta:
        model = SpatialRelationship
        fields = ('rel_class', 'id', 'su1', 'su2', 'type', 'attributes')
        read_only_fields = ('id',)

    def get_rel_class(self, obj):
        return 'spatial'
