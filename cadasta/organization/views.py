from rest_framework.response import Response
from rest_framework import generics
from rest_framework import filters, status

from tutelary.mixins import PermissionRequiredMixin
from accounts.serializers import UserSerializer
from accounts.models import User
from .models import Organization, Project
from .serializers import OrganizationSerializer, ProjectSerializer, \
    UserAdminSerializer
from .mixins import OrganizationUsersQuerySet


class OrganizationList(PermissionRequiredMixin, generics.ListCreateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
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
    serializer_class = OrganizationSerializer
    lookup_field = 'slug'
    permission_required = {
        'GET': 'org.view',
        'PATCH': patch_actions,
    }


class OrganizationUsers(PermissionRequiredMixin,
                        OrganizationUsersQuerySet,
                        generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_required = {
        'GET': 'org.users.list',
        'POST': 'org.users.add',
    }

    def get_perms_objects(self):
        return [self.get_organization(self.kwargs['slug'])]

    def create(self, request, *args, **kwargs):
        try:
            new_user = User.objects.get(username=request.POST['username'])

            org = self.get_organization(self.kwargs['slug'])
            org.users.add(new_user)

            return Response(
                self.serializer_class(new_user).data,
                status=status.HTTP_201_CREATED
            )
        except User.DoesNotExist:
            return Response(
                {'detail': "User with given username does not exist."},
                status=status.HTTP_400_BAD_REQUEST
            )


class OrganizationUsersDetail(PermissionRequiredMixin,
                              OrganizationUsersQuerySet,
                              generics.DestroyAPIView):
    permission_required = 'org.users.remove'

    def get_perms_objects(self):
        return [self.get_organization(self.kwargs['slug'])]

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        self.org.users.remove(user)

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserAdminList(PermissionRequiredMixin, generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('is_active',)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering_fields = ('username', 'first_name', 'last_name')
    permission_required = 'user.view'


class UserAdminDetail(PermissionRequiredMixin, generics.RetrieveUpdateAPIView):
    serializer_class = UserAdminSerializer
    queryset = User.objects.all()
    lookup_field = 'username'
    permission_required = {
        'GET': 'user.view',
        'PATCH': 'user.update'
    }


class ProjectList(PermissionRequiredMixin,  generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
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
        context = super(ProjectList, self).get_serializer_context(*args,
                                                                  **kwargs)
        context['organization'] = org

        return context

    def get_queryset(self):
        return self.get_organization().projects.all()


class ProjectDetail(PermissionRequiredMixin,
                    generics.RetrieveUpdateDestroyAPIView):
    def patch_actions(self, request):
        if hasattr(request, 'data'):
            is_archived = self.get_object().archived
            new_archived = request.data.get('archived', is_archived)
            if not is_archived and (is_archived != new_archived):
                return ('project.update', 'project.archive')
            elif is_archived and (is_archived != new_archived):
                return ('project.update', 'project.unarchive')
        return 'project.update'

    serializer_class = ProjectSerializer
    filter_fields = ('archived',)
    # search_fields = ('name', 'organization', 'country', 'description',)
    # ordering_fields = ('name', 'organization', 'country', 'description',)
    lookup_field = 'project_slug'
    permission_required = {
        'GET': 'project.list',
        'PATCH': patch_actions,
    }

    def get_organization(self):
        if not hasattr(self, 'organization_object'):
            org_slug = self.kwargs['slug']
            self.organization_object = Organization.objects.get(slug=org_slug)

        return self.organization_object

    def get_serializer_context(self, *args, **kwargs):
        org = self.get_organization()
        context = super(ProjectDetail, self).get_serializer_context(*args,
                                                                **kwargs)
        context['organization'] = org

        return context

    def get_queryset(self):
        return self.get_organization().projects.all()


class ProjectDelete(PermissionRequiredMixin, generics.DestroyAPIView):
    queryset = Organization.objects.all()
    permission_required = 'project.resource.delete'


class ProjectUsers(PermissionRequiredMixin,
                   generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_required = {
        'GET': 'project.users.list',
        'POST': 'project.users.add',
    }

    def create(self, request, *args, **kwargs):
        try:
            new_user = User.objects.get(username=request.POST['username'])

            org = self.get_organization(self.kwargs['slug'])
            org.users.add(new_user)

            return Response(
                self.serializer_class(new_user).data,
                status=status.HTTP_201_CREATED
            )
        except User.DoesNotExist:
            return Response(
                {'detail': "User with given username does not exist."},
                status=status.HTTP_400_BAD_REQUEST
            )
