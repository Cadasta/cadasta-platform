from rest_framework import generics, filters, status
from rest_framework.response import Response
from tutelary.mixins import APIPermissionRequiredMixin
from core.mixins import update_permissions

from resources.serializers import ResourceSerializer
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
    lookup_url_kwarg = 'location'
    lookup_field = 'id'
    permission_required = {
        'GET': 'spatial.view',
        'PUT': update_permissions('spatial.update'),
        'PATCH': update_permissions('spatial.update'),
        'DELETE': update_permissions('spatial.delete')
    }

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SpatialUnitResourceList(APIPermissionRequiredMixin,
                              mixins.SpatialUnitResourceMixin,
                              generics.ListCreateAPIView):
    serializer_class = ResourceSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('archived',)
    search_fields = ('name', 'description', 'file',)
    ordering_fields = ('name', 'description', 'file',)
    permission_required = {
        'GET': 'spatial.resources.list',
        'POST': update_permissions('spatial.resources.add')
    }

    def get_perms_objects(self):
        return [self.get_object()]


class SpatialUnitResourceDetail(APIPermissionRequiredMixin,
                                mixins.SpatialUnitResourceMixin,
                                generics.RetrieveUpdateDestroyAPIView):
    def patch_actions(self, request):
        if hasattr(request, 'data'):
            if self.get_object().project.archived:
                return False
            is_archived = self.get_object().archived
            new_archived = request.data.get('archived', is_archived)
            if not is_archived and (is_archived != new_archived):
                return ('spatial.resources.edit', 'spatial.resources.archive')
        return 'spatial.resources.edit'

    serializer_class = ResourceSerializer
    permission_required = {
        'GET': 'spatial.resources.view',
        'PUT': patch_actions,
        'PATCH': patch_actions,
        'DELETE': patch_actions,
    }
    lookup_url_kwarg = 'resource'
    lookup_field = 'id'

    def get_perms_objects(self):
        return [self.get_spatial_unit()]

    def get_object(self):
        return self.get_resource()

    def destroy(self, request, *args, **kwargs):
        return self.detach_resource(self.kwargs['location'])


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
        'PUT': update_permissions('spatial_rel.update'),
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
