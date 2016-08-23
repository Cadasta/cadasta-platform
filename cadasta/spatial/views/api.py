from rest_framework import generics, filters, status
from rest_framework.response import Response
from tutelary.mixins import APIPermissionRequiredMixin
from core.mixins import update_permissions

from spatial import serializers
from . import mixins


class SpatialUnitList(APIPermissionRequiredMixin,
                      mixins.SpatialQuerySetMixin,
                      generics.ListCreateAPIView):
    def get_actions(self, request):
        if self.get_project().archived:
            return ['project.view_archived', 'spatial.list']
        if self.get_project().public():
            return ['project.view', 'spatial.list']
        else:
            return ['project.view_private', 'spatial.list']

    serializer_class = serializers.SpatialUnitSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('type',)

    permission_required = {
        'GET': get_actions,
        'POST': update_permissions('spatial.create'),
    }

    def get_perms_objects(self):
        return [self.get_project()]


class SpatialUnitDetail(APIPermissionRequiredMixin,
                        mixins.SpatialQuerySetMixin,
                        generics.RetrieveUpdateDestroyAPIView):

    serializer_class = serializers.SpatialUnitSerializer
    lookup_url_kwarg = 'spatial_id'
    lookup_field = 'id'
    permission_required = {
        'GET': 'spatial.view',
        'PATCH': update_permissions('spatial.update'),
        'DELETE': update_permissions('spatial.delete')
    }

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SpatialRelationshipCreate(APIPermissionRequiredMixin,
                                mixins.SpatialRelationshipQuerySetMixin,
                                generics.CreateAPIView):

    permission_required = update_permissions('spatial_rel.create')
    serializer_class = serializers.SpatialRelationshipWriteSerializer

    def get_perms_objects(self):
        return [self.get_project()]


class SpatialRelationshipDetail(APIPermissionRequiredMixin,
                                mixins.SpatialRelationshipQuerySetMixin,
                                generics.RetrieveUpdateDestroyAPIView):

    lookup_url_kwarg = 'spatial_rel_id'
    lookup_field = 'id'
    permission_required = {
        'GET': 'spatial_rel.view',
        'PATCH': update_permissions('spatial_rel.update'),
        'DELETE': update_permissions('spatial_rel.delete')
    }

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return serializers.SpatialRelationshipWriteSerializer
        else:
            return serializers.SpatialRelationshipReadSerializer

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
