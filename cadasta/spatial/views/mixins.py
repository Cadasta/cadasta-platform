import json
from django.http import Http404
from django.core.urlresolvers import reverse
from organization.views.mixins import ProjectMixin
from resources.views.mixins import ResourceViewMixin

from ..serializers import SpatialUnitGeoJsonSerializer
from ..models import SpatialUnit


class SpatialQuerySetMixin(ProjectMixin):
    def get_queryset(self):
        self.proj = self.get_project()
        return self.proj.spatial_units.all()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['object'] = self.get_project()
        locations = self.get_queryset()

        if locations.model == SpatialUnit:
            context['geojson'] = json.dumps(
                SpatialUnitGeoJsonSerializer(
                    self.get_queryset(), many=True).data
            )

        return context

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context['project'] = self.get_project()
        return context

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs['project_id'] = self.get_project().id
        return form_kwargs

    def get_success_url(self):
        kwargs = self.kwargs
        kwargs['location'] = self.object.id

        return reverse('locations:detail', kwargs=kwargs)


class SpatialRelationshipQuerySetMixin(ProjectMixin):

    def get_perms_objects(self):
        return [self.get_project()]

    def get_queryset(self):
        self.proj = self.get_project()
        return self.proj.spatial_relationships.all()

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context['project'] = self.get_project()
        return context


class SpatialUnitObjectMixin(SpatialQuerySetMixin):
    def get_object(self):
        try:
            return SpatialUnit.objects.get(
                project__organization__slug=self.kwargs['organization'],
                project__slug=self.kwargs['project'],
                id=self.kwargs['location']
            )
        except SpatialUnit.DoesNotExist as e:
            raise Http404(e)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['location'] = self.get_object()

        locations = self.get_queryset()
        if locations.model == SpatialUnit:
            context['geojson'] = json.dumps(
                SpatialUnitGeoJsonSerializer(
                    locations.exclude(id=context['location'].id),
                    many=True).data
            )
        return context


class SpatialUnitResourceMixin(ResourceViewMixin, SpatialUnitObjectMixin):
    def get_content_object(self):
        return self.get_object()

    def get_success_url(self):
        kwargs = self.kwargs
        kwargs['location'] = self.get_object().id

        return reverse('locations:detail', kwargs=kwargs) + '#resources'


class SpatialUnitRelationshipMixin(SpatialUnitObjectMixin):
    def get_form_kwargs(self, *args, **kwargs):
        kwargs = {
            'project': self.get_project(),
            'spatial_unit': self.get_object()
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        return kwargs
