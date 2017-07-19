from accounts.models import User
from core.mixins import APIPermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import filters, generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from . import mixins
from .. import serializers
from ..models import Organization, OrganizationRole, ProjectRole, Project


class OrganizationList(APIPermissionRequiredMixin,
                       generics.ListCreateAPIView):
    lookup_url_kwarg = 'organization'
    lookup_field = 'slug'
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

    def get_filtered_queryset(self):
        user = self.request.user
        default = Q(access='public', archived=False)
        all_orgs = Organization.objects.all()
        if user.is_superuser:
            return all_orgs
        if user.is_anonymous:
            return all_orgs.filter(default)
        org_roles = user.organizationrole_set.all(
        ).select_related('organization')
        ids = []
        for role in org_roles:
            perms = role.permissions
            org = role.organization
            if ('org.view.private' in perms and
                    org.access == 'private' and not org.archived):
                ids.append(org.id)
            if ('org.view.archived' in perms and org.archived):
                ids.append(org.id)
        default |= Q(id__in=set(ids))
        return all_orgs.filter(default)


class OrganizationDetail(APIPermissionRequiredMixin,
                         mixins.OrganizationMixin,
                         generics.RetrieveUpdateAPIView):
    def view_actions(self, request):
        if self.get_object().archived:
            return 'org.view.archived'
        return 'org.view'

    def patch_actions(self, request):
        if hasattr(request, 'data'):
            is_archived = self.get_object().archived
            new_archived = request.data.get('archived', is_archived)
            if not is_archived and (is_archived != new_archived):
                return ('org.update', 'org.archive')
            elif is_archived and (is_archived != new_archived):
                return ('org.update', 'org.unarchive')
            elif is_archived and (is_archived == new_archived):
                return False
        return 'org.update'

    lookup_url_kwarg = 'organization'
    lookup_field = 'slug'
    org_lookup = 'organization'
    queryset = Organization.objects.all()
    serializer_class = serializers.OrganizationSerializer
    permission_required = {
        'GET': view_actions,
        'PATCH': patch_actions,
        'PUT': patch_actions
    }

    def get_serializer(self, *args, **kwargs):
        if 'org.users.list' not in self.permissions:
            kwargs['hide_detail'] = True
        return super().get_serializer(*args, **kwargs)


class OrganizationUsers(APIPermissionRequiredMixin,
                        mixins.OrganizationRoles,
                        generics.ListCreateAPIView):

    def post_actions(self, request):
        return ('' if self.get_organization().archived else 'org.users.add')

    lookup_url_kwarg = 'organization'
    lookup_field = 'slug'
    serializer_class = serializers.OrganizationUserSerializer
    permission_required = {
        'GET': 'org.users.list',
        'POST': post_actions
    }


class OrganizationUsersDetail(APIPermissionRequiredMixin,
                              mixins.OrganizationRoles,
                              generics.RetrieveUpdateDestroyAPIView):

    serializer_class = serializers.OrganizationUserSerializer
    permission_required = {
        'GET': 'org.users.list',
        'PUT': 'org.users.edit',
        'PATCH': 'org.users.edit',
        'DELETE': 'org.users.remove'
    }

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            raise PermissionDenied
        OrganizationRole.objects.get(
            organization=self.org, user=user
        ).delete()

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
        'PATCH': 'user.update',
        'PUT': 'user.update'
    }


class OrganizationProjectList(APIPermissionRequiredMixin,
                              mixins.OrgRoleCheckMixin,
                              generics.ListCreateAPIView):

    def post_actions(self, request):
        return (
            False if self.get_organization().archived else 'project.create')

    org_lookup = 'organization'
    serializer_class = serializers.ProjectSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('archived',)
    search_fields = ('name', 'organization__name', 'country', 'description',)
    ordering_fields = ('name', 'organization', 'country', 'description',)
    permission_required = {
        'GET': 'project.list',
        'POST': post_actions
    }

    def get_organization(self):
        if not hasattr(self, 'org'):
            self.org = get_object_or_404(Organization,
                                         slug=self.kwargs['organization'])
        return self.org

    def get_perms_objects(self):
        return list(self.get_queryset()) + [self.get_organization()]

    def get_serializer_context(self, *args, **kwargs):
        org = self.get_organization()
        context = super(OrganizationProjectList,
                        self).get_serializer_context(*args, **kwargs)
        context['organization'] = org

        return context

    def get_filtered_queryset(self):
        user = self.request.user
        org = Organization.objects.get(slug=self.kwargs['organization'])
        all_projects = Project.objects.all()
        default = Q(access='public', archived=False)

        if user.is_superuser:
            return all_projects
        if user.is_anonymous:
            default &= Q(organization=org)
            return all_projects.filter(default)

        org_projects = all_projects.filter(organization=org)
        try:
            role = OrganizationRole.objects.get(organization=org, user=user)
            if role.admin:
                return org_projects
            else:
                return org_projects.filter(archived=False)
        except OrganizationRole.DoesNotExist:
            return org_projects.filter(default)


class ProjectList(APIPermissionRequiredMixin,
                  mixins.ProjectListMixin,
                  generics.ListAPIView):

    serializer_class = serializers.ProjectSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('archived',)
    search_fields = ('name', 'organization__name', 'country', 'description',)
    ordering_fields = ('name', 'organization', 'country', 'description',)
    permission_required = {'GET': 'project.list'}


class ProjectDetail(APIPermissionRequiredMixin,
                    mixins.OrganizationMixin,
                    mixins.ProjectMixin,
                    generics.RetrieveUpdateAPIView):
    def get_actions(self, request):
        if self.get_object().archived:
            return 'project.view.archived'
        if self.get_object().public():
            return 'project.view'
        else:
            return 'project.view.private'

    def patch_actions(self, request):
        if hasattr(request, 'data'):
            is_archived = self.get_object().archived
            new_archived = request.data.get('archived', is_archived)
            if not is_archived and (is_archived != new_archived):
                return ('project.update', 'project.archive')
            elif is_archived and (is_archived != new_archived):
                return ('project.update', 'project.unarchive')
            elif is_archived and (is_archived == new_archived):
                return False
        return 'project.update'

    serializer_class = serializers.ProjectSerializer
    filter_fields = ('archived',)
    lookup_url_kwarg = 'project'
    lookup_field = 'slug'
    org_lookup = 'organization'
    permission_required = {
        'GET': get_actions,
        'PATCH': patch_actions,
        'PUT': patch_actions,
    }

    def get_queryset(self):
        return self.get_organization(
            lookup_kwarg='organization').projects.all()

    def get_serializer(self, *args, **kwargs):
        if 'project.users.list' not in self.permissions:
            kwargs['hide_detail'] = True
        return super().get_serializer(*args, **kwargs)


class ProjectUsers(APIPermissionRequiredMixin,
                   mixins.ProjectRoles,
                   generics.ListCreateAPIView):

    serializer_class = serializers.ProjectUserSerializer
    permission_required = {
        'GET': 'project.users.list',
        'POST': 'project.users.add'
    }


class ProjectUsersDetail(APIPermissionRequiredMixin,
                         mixins.ProjectRoles,
                         generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.ProjectUserSerializer

    permission_required = {
        'GET': 'project.users.list',
        'PATCH': 'project.users.update',
        'PUT': 'project.users.update',
        'DELETE': 'project.users.remove',
    }

    def destroy(self, request, *args, **kwargs):
        ProjectRole.objects.get(
            project=self.prj, user=self.get_object()
        ).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
