from django.shortcuts import get_object_or_404

from .models import Organization


class OrganizationMixin:
    def get_organization(self, slug):
        return get_object_or_404(Organization, slug=slug)


class OrganizationUsersQuerySet(OrganizationMixin):
    lookup_field = 'username'

    def get_queryset(self):
        self.org = self.get_organization(self.kwargs['slug'])
        return self.org.users.all()
