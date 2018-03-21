from tutelary.mixins import APIPermissionRequiredMixin
from rest_framework import generics
from rest_framework_gis.pagination import GeoJsonPagination

from . import mixins
from .. import serializers


class Paginator(GeoJsonPagination):
    page_size = 250


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
