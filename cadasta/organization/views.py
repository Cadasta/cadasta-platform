from rest_framework.response import Response
from rest_framework import generics
from rest_framework import filters, status

from tutelary.mixins import PermissionRequiredMixin
from .models import Organization
from . import serializers
from .mixins import OrganizationRoles, ProjectRoles


class OrganizationList(PermissionRequiredMixin, generics.ListCreateAPIView):
    queryset = Organization.objects.all()
    serializer_class = serializers.OrganizationSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('archived',)
    search_fields = ('name', 'description',)
    ordering_fields = ('name', 'description',)
    permission_required = {
        'GET': 'org.list',
        'POST': 'org.create',
    }


class OrganizationDetail(PermissionRequiredMixin,
                         generics.RetrieveUpdateAPIView):
    def patch_actions(self, request):
        if hasattr(request, 'data'):
            is_archived = self.get_object().archived
            new_archived = request.data.get('archived', is_archived)
            if not is_archived and (is_archived != new_archived):
                return ('org.update', 'org.archive')
            elif is_archived and (is_archived != new_archived):
                return ('org.update', 'org.unarchive')
        return 'org.update'

    queryset = Organization.objects.all()
    serializer_class = serializers.OrganizationSerializer
    lookup_field = 'slug'
    permission_required = {
        'GET': 'org.view',
        'PATCH': patch_actions,
    }


class OrganizationUsers(PermissionRequiredMixin,
                        OrganizationRoles,
                        generics.ListCreateAPIView):
    serializer_class = serializers.OrganizationUserSerializer
    permission_required = {
        'GET': 'org.users.list',
        'POST': 'org.users.add',
    }


class OrganizationUsersDetail(PermissionRequiredMixin,
                              OrganizationRoles,
                              generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.OrganizationUserSerializer
    permission_required = 'org.users.remove'

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        role = self.org.users.get(id=user.id)
        role.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectList(PermissionRequiredMixin, generics.ListAPIView):
    serializer_class = serializers.ProjectSerializer
    filter_fields = ('archived',)
    search_fields = ('name', 'organization', 'country', 'description',)
    ordering_fields = ('name', 'organization', 'country', 'description',)
    permission_required = {
        'GET': 'project.list',
        'POST': 'project.create'
    }

    def get_organization(self):
        if not self.organization_object:
            org_slug = self.kwargs['slug']
            self.organization_object = Organization.objects.get(slug=org_slug)

        return self.organization_object

    def get_serializer_context(self, *args, **kwargs):
        org = self.get_organization()
        context = super(ProjectList, self).get_serializer_context(*args, **kwargs)
        context['organization'] = org

        return context

    def get_queryset(self):
        return self.get_organization().projects.all()


class ProjectDetails(PermissionRequiredMixin, generics.ListCreateAPIView):
    queryset = Organization.objects.all()
    filter_fields = ('archived',)
    search_fields = ('name', 'organization', 'country', 'description',)
    ordering_fields = ('name', 'organization', 'country', 'description',)
    permission_required = {
        'GET': 'project.list',
        'POST': 'project.create'
    }


class ProjectDelete(PermissionRequiredMixin, generics.DestroyAPIView):
    queryset = Organization.objects.all()
    permission_required = 'project.resource.delete'


class ProjectUsers(PermissionRequiredMixin,
                   ProjectRoles,
                   generics.ListCreateAPIView):
    serializer_class = serializers.ProjectUserSerializer
    permission_required = {
        'GET': 'project.users.list',
        'POST': 'project.users.add'
    }


class ProjectUsersDetail(PermissionRequiredMixin,
                         ProjectRoles,
                         generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.ProjectUserSerializer

    permission_required = {
        'GET': 'project.users.list',
        'PATCH': 'project.users.add',
        'DELETE': 'project.users.delete'
    }

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        role = self.prj.users.get(id=user.id)
        role.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
