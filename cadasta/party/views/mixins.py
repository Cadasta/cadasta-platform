import json
from django.http import Http404
from django.core.urlresolvers import reverse
from organization.views.mixins import ProjectMixin
from resources.views.mixins import ResourceViewMixin

from spatial.serializers import SpatialUnitGeoJsonSerializer
from ..models import Party, TenureRelationship


class PartyQuerySetMixin(ProjectMixin):
    def get_queryset(self):
        self.proj = self.get_project()
        return self.proj.parties.all()

    def get_serializer_context(self, *args, **kwargs):
        context = super(PartyQuerySetMixin, self).get_serializer_context(
            *args, **kwargs)
        context['project'] = self.get_project()
        return context

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['object'] = self.get_project()
        return context

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs['project_id'] = self.get_project().id
        return form_kwargs

    def get_success_url(self):
        kwargs = self.kwargs
        kwargs['party'] = self.object.id

        return reverse('parties:detail', kwargs=kwargs)


class PartyRelationshipQuerySetMixin(ProjectMixin):
    def get_queryset(self):
        self.proj = self.get_project()
        return self.proj.party_relationships.all()

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context['project'] = self.get_project()
        return context


class TenureRelationshipQuerySetMixin(ProjectMixin):
    def get_queryset(self):
        self.proj = self.get_project()
        return self.proj.tenure_relationships.all()

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context['project'] = self.get_project()
        return context


class PartyObjectMixin(PartyQuerySetMixin):
    def get_object(self):
        try:
            return Party.objects.get(
                project__organization__slug=self.kwargs['organization'],
                project__slug=self.kwargs['project'],
                id=self.kwargs['party']
            )
        except Party.DoesNotExist as e:
            raise Http404(e)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['party'] = self.get_object()
        return context


class PartyResourceMixin(ResourceViewMixin, PartyObjectMixin):
    def get_content_object(self):
        return self.get_object()

    def get_success_url(self):
        kwargs = self.kwargs
        kwargs['party'] = self.get_object().id

        return reverse('parties:detail', kwargs=kwargs)


class PartyRelationshipObjectMixin(ProjectMixin):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['object'] = self.get_project()
        context['relationship'] = self.get_object()
        context['location'] = self.get_object().spatial_unit

        locations = context['object'].spatial_units.exclude(
            id=context['location'].id)

        context['geojson'] = json.dumps(
            SpatialUnitGeoJsonSerializer(locations, many=True).data
        )

        return context

    def get_queryset(self):
        self.proj = self.get_project()
        return self.proj.tenure_relationships.all()

    def get_object(self):
        try:
            return TenureRelationship.objects.get(
                project__organization__slug=self.kwargs['organization'],
                project__slug=self.kwargs['project'],
                id=self.kwargs['relationship']
            )
        except TenureRelationship.DoesNotExist as e:
            raise Http404(e)


class PartyRelationshipResourceMixin(ResourceViewMixin,
                                     PartyRelationshipObjectMixin):
    def get_content_object(self):
        return self.get_object()

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = {
            'project_id': self.get_project().id,
            'content_object': self.get_object(),
            'contributor': self.request.user
        }

        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST

        return kwargs

    def get_success_url(self):
        return reverse('parties:relationship_detail', kwargs=self.kwargs)
