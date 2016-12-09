from django.http import Http404
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from organization.views.mixins import ProjectMixin
from resources.views.mixins import ResourceViewMixin
from resources.models import Resource

from ..models import SpatialUnit


class SpatialQuerySetMixin(ProjectMixin):
    def get_queryset(self):
        self.proj = self.get_project()
        if not hasattr(self, '_queryset'):
            self._queryset = self.proj.spatial_units.all().order_by('id')
        return self._queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['object'] = self.get_project()
        return context

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context['project'] = self.get_project()
        return context

    def get_success_url(self):
        kwargs = self.kwargs
        kwargs['location'] = self.object.id
        return reverse('locations:detail', kwargs=kwargs)


class SpatialRelationshipQuerySetMixin(ProjectMixin):
    def get_queryset(self):
        self.proj = self.get_project()
        return self.proj.spatial_relationships.all()

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context['project'] = self.get_project()
        return context


class SpatialUnitObjectMixin(SpatialQuerySetMixin):
    def get_object(self):
        if not hasattr(self, '_obj'):
            self._obj = get_object_or_404(
                SpatialUnit,
                project__organization__slug=self.kwargs['organization'],
                project__slug=self.kwargs['project'],
                id=self.kwargs['location']
            )
        return self._obj

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['location'] = self.get_object()
        return context


class SpatialUnitResourceMixin(ResourceViewMixin, SpatialUnitObjectMixin):
    def get_content_object(self):
        return self.get_object()

    def get_success_url(self):
        kwargs = self.kwargs
        kwargs['location'] = self.get_object().id
        return reverse('locations:detail', kwargs=kwargs) + '#resources'

    def get_model_context(self):
        context = super().get_model_context()
        context['project_id'] = self.get_project().id
        return context

    def get_spatial_unit(self):
        if not hasattr(self, 'spatial_unit_object'):
            self.spatial_unit_object = get_object_or_404(
                SpatialUnit,
                project__organization__slug=self.kwargs['organization'],
                project__slug=self.kwargs['project'],
                id=self.kwargs['location']
            )
        return self.spatial_unit_object

    def get_resource(self):
        if not hasattr(self, 'resource_object'):
            try:
                self.resource_object = self.get_spatial_unit().resources.get(
                    id=self.kwargs['resource'])
            except Resource.DoesNotExist as e:
                raise Http404(e)
        return self.resource_object


class SpatialUnitRelationshipMixin(SpatialUnitObjectMixin):
    def get_form_kwargs(self, *args, **kwargs):
        kwargs = {
            'project': self.get_project(),
            'spatial_unit': self.get_object()
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        return kwargs
