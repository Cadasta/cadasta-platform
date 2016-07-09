import json
from jsonattrs.mixins import JsonAttrsMixin
from django.views import generic
from django.core.urlresolvers import reverse

from core.mixins import LoginPermissionRequiredMixin

from resources.forms import AddResourceFromLibraryForm
from party.models import TenureRelationship
from party.messages import TENURE_REL_CREATE
from . import mixins
from .. import forms
from ..serializers import SpatialUnitGeoJsonSerializer
from .. import messages as error_messages


class LocationsList(LoginPermissionRequiredMixin,
                    mixins.SpatialQuerySetMixin,
                    generic.ListView):
    template_name = 'spatial/location_map.html'
    permission_required = 'spatial.list'
    permission_denied_message = error_messages.SPATIAL_LIST
    permission_filter_queryset = ('spatial.view',)


class LocationsAdd(LoginPermissionRequiredMixin,
                   mixins.SpatialQuerySetMixin,
                   generic.CreateView):
    form_class = forms.LocationForm
    template_name = 'spatial/location_add.html'
    permission_required = 'spatial.add'
    permission_denied_message = error_messages.SPATIAL_CREATE

    def get_perms_objects(self):
        return [self.get_project()]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        prj = self.get_project()

        kwargs['schema_selectors'] = (
            {'name': 'organization',
             'value': prj.organization,
             'selector': prj.organization.id},
            {'name': 'project',
             'value': prj,
             'selector': prj.id},
            {'name': 'questionaire',
             'value': prj.current_questionnaire,
             'selector': prj.current_questionnaire}
        )

        return kwargs


class LocationDetail(LoginPermissionRequiredMixin,
                     JsonAttrsMixin,
                     mixins.SpatialUnitObjectMixin,
                     generic.DetailView):
    template_name = 'spatial/location_detail.html'
    permission_required = 'spatial.view'
    permission_denied_message = error_messages.SPATIAL_VIEW
    attributes_field = 'attributes'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['relationships'] = TenureRelationship.objects.filter(
            spatial_unit=context['location'])
        return context


class LocationEdit(LoginPermissionRequiredMixin,
                   mixins.SpatialUnitObjectMixin,
                   generic.UpdateView):
    template_name = 'spatial/location_edit.html'
    form_class = forms.LocationForm
    permission_required = 'spatial.edit'
    permission_denied_message = error_messages.SPATIAL_UPDATE


class LocationDelete(LoginPermissionRequiredMixin,
                     mixins.SpatialUnitObjectMixin,
                     generic.DeleteView):
    template_name = 'spatial/location_delete.html'
    permission_required = 'spatial.delete'
    permission_denied_message = error_messages.SPATIAL_DELETE

    def get_success_url(self):
        kwargs = self.kwargs
        del kwargs['location']
        return reverse('locations:list', kwargs=self.kwargs)


class LocationResourceAdd(LoginPermissionRequiredMixin,
                          mixins.SpatialUnitResourceMixin,
                          generic.edit.FormMixin,
                          generic.DetailView):
    template_name = 'spatial/resources_add.html'
    form_class = AddResourceFromLibraryForm
    permission_required = 'spatial.resources.add'
    permission_denied_message = error_messages.SPATIAL_ADD_RESOURCE

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)


class LocationResourceNew(LoginPermissionRequiredMixin,
                          mixins.SpatialUnitResourceMixin,
                          generic.CreateView):
    template_name = 'spatial/resources_new.html'
    permission_required = 'spatial.resources.add'
    permission_denied_message = error_messages.SPATIAL_ADD_RESOURCE

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        project_locations = context['object'].spatial_units
        context['geojson'] = json.dumps(
            SpatialUnitGeoJsonSerializer(
                project_locations.exclude(id=context['location'].id),
                many=True).data
        )
        return context


class TenureRelationshipAdd(LoginPermissionRequiredMixin,
                            mixins.SpatialUnitRelationshipMixin,
                            generic.CreateView):
    template_name = 'spatial/relationship_add.html'
    form_class = forms.TenureRelationshipForm
    permission_required = 'tenure_rel.create'
    permission_denied_message = TENURE_REL_CREATE

    def get_perms_objects(self):
        return [self.get_project()]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context['geojson'] = json.dumps(
            SpatialUnitGeoJsonSerializer(self.get_queryset(), many=True).data
        )

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        prj = self.get_project()

        kwargs['schema_selectors'] = (
            {'name': 'organization',
             'value': prj.organization,
             'selector': prj.organization.id},
            {'name': 'project',
             'value': prj,
             'selector': prj.id},
            {'name': 'questionaire',
             'value': prj.current_questionnaire,
             'selector': prj.current_questionnaire}
        )

        return kwargs

    def get_success_url(self):
        return (reverse('locations:detail', kwargs=self.kwargs) +
                '#relationships')
