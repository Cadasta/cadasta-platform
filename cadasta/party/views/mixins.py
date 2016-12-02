from django.http import Http404
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from organization.views.mixins import ProjectMixin
from resources.views.mixins import ResourceViewMixin
from resources.models import Resource

from party.models import Party, TenureRelationship


class PartyQuerySetMixin(ProjectMixin):
    def get_queryset(self):
        self.proj = self.get_project()
        parties = self.proj.parties.all()
        if (
            hasattr(self, 'no_jsonattrs_in_queryset') and
            self.no_jsonattrs_in_queryset
        ):
            parties = parties.only('id', 'name', 'type', 'project')
        return parties

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
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


class PartyObjectMixin(PartyQuerySetMixin):
    def get_object(self):
        if not hasattr(self, '_obj'):
            self._obj = get_object_or_404(
                Party,
                project__organization__slug=self.kwargs['organization'],
                project__slug=self.kwargs['project'],
                id=self.kwargs['party']
            )
        return self._obj

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

    def get_party(self):
        if not hasattr(self, 'party_object'):
            prj_slug = self.kwargs['project']
            party_id = self.kwargs['party']

            self.party_object = get_object_or_404(
                Party,
                project__slug=prj_slug,
                id=party_id
            )

        return self.party_object

    def get_resource(self):
        if not hasattr(self, 'resource_object'):
            try:
                self.resource_object = self.get_party().resources.get(
                    id=self.kwargs['resource'])
            except Resource.DoesNotExist as e:
                raise Http404(e)
        return self.resource_object

    def get_model_context(self):
        context = super().get_model_context()
        context['project_id'] = self.get_project().id
        return context


class PartyRelationshipObjectMixin(ProjectMixin):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['object'] = self.get_project()
        context['relationship'] = self.get_object()
        context['location'] = self.get_object().spatial_unit

        return context

    def get_object(self):
        if not hasattr(self, '_obj'):
            self._obj = get_object_or_404(
                TenureRelationship,
                project__organization__slug=self.kwargs['organization'],
                project__slug=self.kwargs['project'],
                id=self.kwargs['relationship']
            )
        return self._obj


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


class TenureRelationshipQuerySetMixin(ProjectMixin):
    def get_queryset(self):
        self.proj = self.get_project()
        return self.proj.tenure_relationships.all()

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context['project'] = self.get_project()
        return context


class TenureRelationshipResourceMixin(ResourceViewMixin,
                                      TenureRelationshipQuerySetMixin):
    def get_object(self):
        if not hasattr(self, '_obj'):
            self._obj = get_object_or_404(
                TenureRelationship,
                project__organization__slug=self.kwargs['organization'],
                project__slug=self.kwargs['project'],
                id=self.kwargs['tenure_rel_id']
            )
        return self._obj

    def get_content_object(self):
        return self.get_object()

    def get_tenure_relationship(self):
        if not hasattr(self, 'tenure_object'):
            prj_slug = self.kwargs['project']
            tenure_id = self.kwargs['tenure_rel_id']

            self.tenure_object = get_object_or_404(
                TenureRelationship,
                project__slug=prj_slug,
                id=tenure_id
            )

        return self.tenure_object

    def get_model_context(self):
        context = super().get_model_context()
        context['project_id'] = self.get_project().id
        return context

    def get_resource(self):
        if not hasattr(self, 'resource_object'):
            try:
                self.resource_object = self.get_tenure_relationship(
                    ).resources.get(
                    id=self.kwargs['resource'])
            except Resource.DoesNotExist as e:
                raise Http404(e)
        return self.resource_object
