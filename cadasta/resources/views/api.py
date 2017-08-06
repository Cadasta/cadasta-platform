from django.contrib.contenttypes.models import ContentType
from django.db.models import Exists, OuterRef
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from tutelary.mixins import APIPermissionRequiredMixin

from core.mixins import update_permissions
from resources.models import ContentObject

from . import mixins
from .. import serializers


def patch_actions(self, request):
        if hasattr(request, 'data'):
            if self.get_object().project.archived:
                return False
            is_archived = self.get_object().archived
            new_archived = request.data.get('archived', is_archived)
            if not is_archived and (is_archived != new_archived):
                return ('resource.edit', 'resource.archive')
            elif is_archived and (is_archived != new_archived):
                return ('resource.edit', 'resource.unarchive')
        return 'resource.edit'


def filter_archived_resources(self, view, obj):
        if obj.archived:
            return ('resource.view', 'resource.unarchive')
        else:
            return ('resource.view',)


class ProjectResources(APIPermissionRequiredMixin,
                       mixins.ProjectResourceMixin,
                       generics.ListCreateAPIView):
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('archived',)
    search_fields = ('name', 'description', 'file',)
    ordering_fields = ('name', 'description', 'file',
                       'contributor__username', 'last_updated')
    permission_required = {
        'GET': 'resource.list',
        'POST': update_permissions('resource.add')
    }

    serializer_class = serializers.ResourceSerializer
    permission_filter_queryset = filter_archived_resources
    use_resource_library_queryset = True

    def get_queryset(self):
        proj = self.get_content_object()
        related_content_objs = ContentObject.objects.filter(
            resource=OuterRef('id'),
            content_type=ContentType.objects.get_for_model(proj),
            object_id=proj.id)
        return super().get_queryset().prefetch_related(
            'content_objects__content_type').annotate(
            attached=Exists(related_content_objs))


class ProjectResourcesDetail(APIPermissionRequiredMixin,
                             mixins.ResourceObjectMixin,
                             generics.RetrieveUpdateAPIView):

    lookup_url_kwarg = 'resource'
    permission_required = {
        'GET': 'resource.view',
        'PUT': patch_actions,
        'PATCH': patch_actions
    }
    use_resource_library_queryset = True


class ProjectSpatialResources(APIPermissionRequiredMixin,
                              mixins.ProjectSpatialResourceMixin,
                              generics.ListAPIView):

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('id', 'name')
    search_fields = ('id', 'name',)
    ordering_fields = ('name')
    permission_required = {
        'GET': 'resource.list'
    }
    permission_filter_queryset = filter_archived_resources


class ProjectSpatialResourcesDetail(APIPermissionRequiredMixin,
                                    mixins.ResourceObjectMixin,
                                    generics.RetrieveUpdateAPIView):

    lookup_url_kwarg = 'resource'
    permission_required = {
        'GET': 'resource.view',
        'PUT': patch_actions,
        'PATCH': patch_actions,
    }
