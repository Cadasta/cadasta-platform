from django.shortcuts import get_object_or_404

from .models import Organization, Project


class OrganizationMixin:
    def get_organization(self, slug):
        return get_object_or_404(Organization, slug=slug)


class OrganizationUsersQuerySet(OrganizationMixin):
    lookup_field = 'username'

    def get_queryset(self):
        self.org = self.get_organization(self.kwargs['slug'])
        return self.org.users.all()


class ProjectMixin:
    def get_project(self):
        return get_object_or_404(
            Project,
            organization__slug=self.kwargs['slug'],
            pk=self.kwargs['project_id']
        )


class ProjectUsersQuerySet(ProjectMixin):
    lookup_field = 'username'

    def get_queryset(self):
        self.prj = self.get_project()
        return self.prj.users.all()
