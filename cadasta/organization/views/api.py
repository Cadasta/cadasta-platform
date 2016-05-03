from rest_framework.response import Response
from rest_framework import generics
from rest_framework import filters, status

from tutelary.mixins import APIPermissionRequiredMixin

from accounts.models import User

from ..models import Organization
from .. import serializers
from .mixins import OrganizationRoles, ProjectRoles, ProjectQuerySetMixin


class OrganizationList(APIPermissionRequiredMixin, generics.ListCreateAPIView):
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
    permission_filter_queryset = ('org.view',)


class OrganizationDetail(APIPermissionRequiredMixin,
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


class OrganizationUsers(APIPermissionRequiredMixin,
                        OrganizationRoles,
                        generics.ListCreateAPIView):
    serializer_class = serializers.OrganizationUserSerializer
    permission_required = {
        'GET': 'org.users.list',
        'POST': 'org.users.add',
    }


class OrganizationUsersDetail(APIPermissionRequiredMixin,
                              OrganizationRoles,
                              generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.OrganizationUserSerializer
    permission_required = 'org.users.remove'

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        role = self.org.users.get(id=user.id)
        role.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserAdminList(APIPermissionRequiredMixin, generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = serializers.UserAdminSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('is_active',)
    search_fields = ('username', 'full_name', 'email')
    ordering_fields = ('username', 'full_name')
    permission_required = 'user.list'


class UserAdminDetail(APIPermissionRequiredMixin,
                      generics.RetrieveUpdateAPIView):
    serializer_class = serializers.UserAdminSerializer
    queryset = User.objects.all()
    lookup_field = 'username'
    permission_required = {
        'GET': 'user.list',
        'PATCH': 'user.update'
    }


class OrganizationProjectList(APIPermissionRequiredMixin,
                              ProjectQuerySetMixin,
                              generics.ListCreateAPIView):
    serializer_class = serializers.ProjectSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('archived',)
    search_fields = ('name', 'organization__name', 'country', 'description',)
    ordering_fields = ('name', 'organization', 'country', 'description',)
    permission_required = {
        'GET': 'project.list',
        'POST': 'project.create'
    }

    def get_organization(self):
        if not hasattr(self, 'organization_object'):
            org_slug = self.kwargs['slug']
            self.organization_object = Organization.objects.get(slug=org_slug)

        return self.organization_object

    def get_perms_objects(self):
        return [self.get_organization()]

    def get_serializer_context(self, *args, **kwargs):
        org = self.get_organization()
        context = super(OrganizationProjectList,
                        self).get_serializer_context(*args, **kwargs)
        context['organization'] = org

        return context

    def get_queryset(self):
        return super().get_queryset().filter(
            organization__slug=self.kwargs['slug']
        )


class ProjectList(APIPermissionRequiredMixin, ProjectQuerySetMixin,
                  generics.ListAPIView):
    serializer_class = serializers.ProjectSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('archived',)
    search_fields = ('name', 'organization__name', 'country', 'description',)
    ordering_fields = ('name', 'organization', 'country', 'description',)
    permission_required = {'project.list'}


class ProjectDetail(APIPermissionRequiredMixin,
                    generics.RetrieveUpdateDestroyAPIView):
    def get_actions(self, request):
        if self.get_object().public():
            return 'project.view'
        else:
            return 'project.view_private'

    def patch_actions(self, request):
        if hasattr(request, 'data'):
            is_archived = self.get_object().archived
            new_archived = request.data.get('archived', is_archived)
            if not is_archived and (is_archived != new_archived):
                return ('project.update', 'project.archive')
            elif is_archived and (is_archived != new_archived):
                return ('project.update', 'project.unarchive')
        return 'project.update'

    serializer_class = serializers.ProjectSerializer
    filter_fields = ('archived',)
    # search_fields = ('name', 'organization', 'country', 'description',)
    # ordering_fields = ('name', 'organization', 'country', 'description',)
    lookup_url_kwarg = 'project_slug'
    lookup_field = 'slug'
    permission_required = {
        'GET': get_actions,
        'PATCH': patch_actions,
    }

    def get_organization(self):
        if not hasattr(self, 'organization_object'):
            org_slug = self.kwargs['slug']
            self.organization_object = Organization.objects.get(slug=org_slug)

        return self.organization_object

    def get_serializer_context(self, *args, **kwargs):
        org = self.get_organization()
        context = super(ProjectDetail,
                        self).get_serializer_context(*args, **kwargs)
        context['organization'] = org

        return context

    def get_queryset(self):
        return self.get_organization().projects.all()


class ProjectUsers(APIPermissionRequiredMixin,
                   ProjectRoles,
                   generics.ListCreateAPIView):
    serializer_class = serializers.ProjectUserSerializer
    permission_required = {
        'GET': 'project.users.list',
        'POST': 'project.users.add'
    }


class ProjectUsersDetail(APIPermissionRequiredMixin,
                         ProjectRoles,
                         generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.ProjectUserSerializer

    permission_required = {
        'GET': 'project.users.list',
        'PATCH': 'project.users.edit',
        'DELETE': 'project.users.delete'
    }

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        role = self.prj.users.get(id=user.id)
        role.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
