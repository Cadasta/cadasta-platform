from rest_framework import generics, filters
from tutelary.mixins import APIPermissionRequiredMixin
from core.views.mixins import SuperUserCheckMixin
from .mixins import ProjectResourceMixin


class ProjectResources(APIPermissionRequiredMixin,
                       SuperUserCheckMixin,
                       ProjectResourceMixin,
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
    permission_filter_queryset = ('resource.view',)
    use_resource_library_queryset = True


class ProjectResourcesDetail(APIPermissionRequiredMixin,
                             SuperUserCheckMixin,
                             ProjectResourceMixin,
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
