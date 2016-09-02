from rest_framework import filters, generics
from tutelary.mixins import APIPermissionRequiredMixin
from . import mixins


class ProjectResources(APIPermissionRequiredMixin,
                       mixins.ProjectResourceMixin,
                       generics.ListCreateAPIView):
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('archived',)
    search_fields = ('name', 'description', 'file',)
    ordering_fields = ('name', 'description', 'file',)
    permission_required = {
        'GET': 'resource.list',
        'POST': 'resource.add'
    }

    def filter_archived_resources(self, view, obj):
        if obj.archived:
            return ('resource.view', 'resource.unarchive')
        else:
            return ('resource.view',)

    permission_filter_queryset = filter_archived_resources
    use_resource_library_queryset = True


class ProjectResourcesDetail(APIPermissionRequiredMixin,
                             mixins.ResourceObjectMixin,
                             generics.RetrieveUpdateAPIView):

    def patch_actions(self, request):
        if hasattr(request, 'data'):
            is_archived = self.get_object().archived
            new_archived = request.data.get('archived', is_archived)
            if not is_archived and (is_archived != new_archived):
                return ('resource.edit', 'resource.archive')
            elif is_archived and (is_archived != new_archived):
                return ('resource.edit', 'resource.unarchive')
        return 'resource.edit'

    lookup_url_kwarg = 'resource'
    permission_required = {
        'GET': 'resource.view',
        'PATCH': patch_actions
    }
    use_resource_library_queryset = True


class ProjectSpatialResources(APIPermissionRequiredMixin,
                              mixins.ProjectSpatialResourceMixin,
                              generics.ListAPIView):

    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('id', 'name')
    search_fields = ('id', 'name',)
    ordering_fields = ('name')
    permission_required = {
        'GET': 'resource.list'
    }
    permission_filter_queryset = ('resource.view',)
