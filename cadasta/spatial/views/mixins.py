from django.shortcuts import get_object_or_404

from organization.models import Project


class SpatialMixin:

    def get_project(self):
        return get_object_or_404(
            Project,
            organization__slug=self.kwargs['organization'],
            slug=self.kwargs['project_slug']
        )


class SpatialQuerySetMixin(SpatialMixin):

    def get_perms_objects(self):
        return [self.get_project()]

    def get_queryset(self):
        self.proj = self.get_project()
        return self.proj.spatial_units.all()

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context['project'] = self.get_project()
        return context


class SpatialRelationshipQuerySetMixin(SpatialMixin):

    def get_perms_objects(self):
        return [self.get_project()]

    def get_queryset(self):
        self.proj = self.get_project()
        return self.proj.spatial_relationships.all()

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context['project'] = self.get_project()
        return context
