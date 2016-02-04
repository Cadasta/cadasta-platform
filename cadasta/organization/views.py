from rest_framework.response import Response
from rest_framework import generics
from rest_framework import filters, status

from core.views import PermissionRequiredMixin
from accounts.serializers import UserSerializer
from accounts.models import User
from .models import Organization
from .serializers import OrganizationSerializer
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


class OrganizationDetail(PermissionRequiredMixin,
                         generics.RetrieveUpdateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    lookup_field = 'slug'
    permission_required = {
        'GET': 'org.view',
        'PATCH': 'org.update',
    }

    def initial(self, request, *args, **kwargs):
        if hasattr(request, 'data'):
            is_archived = self.get_object().archived
            new_archived = request.data.get('archived', is_archived)

            if not is_archived and (is_archived != new_archived):
                # Add required permission when archiving
                self.add_permission_required = ('org.archive', )
            elif is_archived and (is_archived != new_archived):
                # Add required permission when unarchiving
                self.add_permission_required = ('org.unarchive', )

        return super(OrganizationDetail, self).initial(
            request, *args, **kwargs)


class OrganizationUsers(PermissionRequiredMixin,
                        OrganizationUsersQuerySet,
                        generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_required = {
        'GET': 'org.users.list',
        'POST': 'org.users.add',
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


class OrganizationUsersDetail(PermissionRequiredMixin,
                              OrganizationUsersQuerySet,
                              generics.DestroyAPIView):
    permission_required = 'org.users.remove'

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        self.org.users.remove(user)

        return Response(status=status.HTTP_204_NO_CONTENT)
