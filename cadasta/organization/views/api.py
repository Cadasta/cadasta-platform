from accounts.models import User
from core.mixins import APIPermissionRequiredMixin, PermissionFilterMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import filters, generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from . import mixins
from .. import serializers
from ..models import Organization, OrganizationRole, ProjectRole, Project


class OrganizationList(PermissionFilterMixin,
                       APIPermissionRequiredMixin,
                       mixins.OrganizationListMixin,
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

    def permission_filter_queryset(self):
        if hasattr(self, 'permission_filter'):
            actions = self.permission_filter
            return self.get_filtered_queryset().filter(
                organizationrole__user=self.request.user,
                organizationrole__group__permissions__codename__in=actions)
        return self.get_filtered_queryset()


class OrganizationDetail(APIPermissionRequiredMixin,
                         mixins.OrganizationMixin,
                         generics.RetrieveUpdateAPIView):

    lookup_url_kwarg = 'organization'
    lookup_field = 'slug'
    org_lookup = 'organization'
    queryset = Organization.objects.all()
    serializer_class = serializers.OrganizationSerializer

    def get_permission_required(self):
        request = self.request
        if request.method == 'GET':
            if self.get_object().archived:
                return ('org.view.archived',)
            return ('org.view',)
        if request.method in ['PATCH', 'PUT']:
            if hasattr(request, 'data'):
                is_archived = self.get_object().archived
                new_archived = request.data.get('archived', is_archived)
                if not is_archived and (is_archived != new_archived):
                    return ('org.update', 'org.archive')
                elif is_archived and (is_archived != new_archived):
                    return ('org.update', 'org.unarchive')
                elif is_archived and (is_archived == new_archived):
                    return False
            return ('org.update',)

    def get_serializer(self, *args, **kwargs):
        if 'org.users.list' not in self.permissions:
            kwargs['hide_detail'] = True
        return super().get_serializer(*args, **kwargs)


class OrganizationUsers(APIPermissionRequiredMixin,
                        mixins.OrganizationRoles,
                        generics.ListCreateAPIView):

    lookup_url_kwarg = 'organization'
    lookup_field = 'slug'
    serializer_class = serializers.OrganizationUserSerializer

    def get_permission_required(self):
        request = self.request
        if request.method == 'GET':
            return ('org.users.list',)
        if request.method == 'POST':
            return (() if self.get_organization().archived else
                    ('org.users.add',))


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


class OrganizationProjectList(PermissionFilterMixin,
                              APIPermissionRequiredMixin,
                              mixins.OrgRoleCheckMixin,
                              generics.ListCreateAPIView):

    org_lookup = 'organization'
    serializer_class = serializers.ProjectSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('archived',)
    search_fields = ('name', 'organization__name', 'country', 'description',)
    ordering_fields = ('name', 'organization', 'country', 'description',)

    def get_permission_required(self):
        request = self.request
        if request.method == 'GET':
            return ('project.list',)
        if request.method == 'POST':
            return (() if self.get_organization().archived else
                    ('project.create',))

    def get_organization(self):
        if not hasattr(self, 'org'):
            self.org = get_object_or_404(Organization,
                                         slug=self.kwargs['organization'])
        return self.org

    def get_serializer_context(self, *args, **kwargs):
        org = self.get_organization()
        context = super(OrganizationProjectList,
                        self).get_serializer_context(*args, **kwargs)
        context['organization'] = org

        return context

    def get_filtered_queryset(self):
        user = self.request.user
        org = Organization.objects.get(slug=self.kwargs['organization'])
        org_projects = Project.objects.filter(organization=org)
        default = Q(access='public', archived=False)
        if user.is_superuser or self.is_administrator:
            return org_projects
        if user.is_anonymous:
            return org_projects.filter(default)

        prj_roles = user.projectrole_set.filter(
            project__organization=org).select_related('project')
        if prj_roles:
            ids = []
            ids += (prj_roles.filter(
                project__access='private', project__archived=False,
                group__permissions__codename__in=('project.view.private',))
                .values_list('project', flat=True))
            ids += (prj_roles.filter(
                project__archived=True,
                group__permissions__codename__in=('project.view.archived',))
                .values_list('project', flat=True))
            query = default | Q(id__in=set(ids))
            return org_projects.filter(query)

        if self.is_member:
            query = default | Q(access='private', archived=False)
            return org_projects.filter(query)

        return org_projects.filter(default)

    def permission_filter_queryset(self):
        if hasattr(self, 'permission_filter'):
            actions = self.permission_filter
            return self.get_filtered_queryset().filter(
                projectrole__user=self.request.user,
                projectrole__group__permissions__codename__in=actions)
        return self.get_filtered_queryset()


class ProjectList(PermissionFilterMixin,
                  APIPermissionRequiredMixin,
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

    def permission_filter_queryset(self):
        if hasattr(self, 'permission_filter'):
            actions = self.permission_filter
            return self.get_filtered_queryset().filter(
                projectrole__user=self.request.user,
                projectrole__group__permissions__codename__in=actions)
        return self.get_filtered_queryset()


class ProjectDetail(APIPermissionRequiredMixin,
                    mixins.OrganizationMixin,
                    mixins.ProjectMixin,
                    generics.RetrieveUpdateAPIView):

    serializer_class = serializers.ProjectSerializer
    filter_fields = ('archived',)
    lookup_url_kwarg = 'project'
    lookup_field = 'slug'
    org_lookup = 'organization'

    def get_permission_required(self):
        request = self.request
        if request.method == 'GET':
            if self.get_object().archived:
                return ('project.view.archived',)
            if self.get_object().public():
                return ('project.view',)
            else:
                return ('project.view.private',)
        if request.method in ['PATCH', 'PUT']:
            if hasattr(request, 'data'):
                is_archived = self.get_object().archived
                new_archived = request.data.get('archived', is_archived)
                if not is_archived and (is_archived != new_archived):
                    return ('project.update', 'project.archive')
                elif is_archived and (is_archived != new_archived):
                    return ('project.update', 'project.unarchive')
                elif is_archived and (is_archived == new_archived):
                    return ()
            return ('project.update',)

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
