from django.shortcuts import get_object_or_404

from organization.models import Project


class PartyMixin:

    def get_project(self):
        return get_object_or_404(
            Project,
            organization__slug=self.kwargs['organization'],
            slug=self.kwargs['project_slug']
        )


class PartyQuerySetMixin(PartyMixin):

    def get_perms_objects(self):
        return [self.get_project()]

    def get_queryset(self):
        self.proj = self.get_project()
        print(self.proj.parties.all())
        return self.proj.parties.all()

    def get_serializer_context(self, *args, **kwargs):
        context = super(PartyQuerySetMixin, self).get_serializer_context(
            *args, **kwargs)
        context['project'] = self.get_project()
        return context
