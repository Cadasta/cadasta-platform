from django.shortcuts import get_object_or_404

from .models import Organization, Project


class OrganizationMixin:
    def get_organization(self):
        return get_object_or_404(Organization, slug=self.kwargs['slug'])


class OrganizationRoles(OrganizationMixin):
    lookup_field = 'username'

    def get_queryset(self):
        self.org = self.get_organization()
        return self.org.users.all()

    def get_serializer_context(self, *args, **kwargs):
        context = super(OrganizationRoles, self).get_serializer_context(
            *args, **kwargs)
        context['organization'] = self.get_organization()
        return context

    def get_perms_objects(self):
        return [self.get_organization()]


class ProjectMixin:
    def get_project(self):
        return get_object_or_404(
            Project,
            organization__slug=self.kwargs['slug'],
            pk=self.kwargs['project_id']
        )


class ProjectRoles(ProjectMixin):
    lookup_field = 'username'

    def get_queryset(self):
        self.prj = self.get_project()
        return self.prj.users.all()

    def get_serializer_context(self, *args, **kwargs):
        context = super(ProjectRoles, self).get_serializer_context(
            *args, **kwargs)
        context['project'] = self.get_project()

        return context
