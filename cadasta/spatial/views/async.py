import math
from django.contrib.gis.geos import Polygon
from tutelary.mixins import APIPermissionRequiredMixin
from rest_framework import generics
from rest_framework_gis.pagination import GeoJsonPagination

from . import mixins
from .. import serializers


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int(
        (1.0 - math.log(math.tan(lat_rad) +
         (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return [xtile, ytile]


def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return [lon_deg, lat_deg]


class Paginator(GeoJsonPagination):
    page_size = 1000


class SpatialUnitList(APIPermissionRequiredMixin,
                      mixins.SpatialQuerySetMixin,
                      generics.ListAPIView):
    pagination_class = Paginator
    serializer_class = serializers.SpatialUnitGeoJsonSerializer

    def get_actions(self, request):
        if self.get_project().archived:
            return ['project.view_archived', 'spatial.list']
        if self.get_project().public():
            return ['project.view', 'spatial.list']
        else:
            return ['project.view_private', 'spatial.list']

    permission_required = {
        'GET': get_actions
    }

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        return queryset.exclude(id=self.request.GET.get('exclude'))

    def get_perms_objects(self):
        return [self.get_project()]


class SpatialUnitTiles(APIPermissionRequiredMixin,
                       mixins.SpatialQuerySetMixin,
                       generics.ListAPIView):

    serializer_class = serializers.SpatialUnitGeoJsonSerializer

    def get_actions(self, request):
        if self.get_project().archived:
            return ['project.view_archived', 'spatial.list']
        if self.get_project().public():
            return ['project.view', 'spatial.list']
        else:
            return ['project.view_private', 'spatial.list']

    permission_required = {
        'GET': get_actions
    }

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        x = int(self.kwargs['x'])
        y = int(self.kwargs['y'])
        zoom = int(self.kwargs['z'])

        bbox = num2deg(xtile=x, ytile=y, zoom=zoom)
        bbox.extend(num2deg(xtile=x+1, ytile=y+1, zoom=zoom))
        bbox = Polygon.from_bbox(bbox)
        final_queryset = queryset.filter(
            geometry__intersects=bbox).exclude(
            id=self.request.GET.get('exclude'))

        return final_queryset

    def get_perms_objects(self):
        return [self.get_project()]
