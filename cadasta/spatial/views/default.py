import json
from jsonattrs.mixins import JsonAttrsMixin
import django.views.generic as base_generic
from core.views import generic
from django.core.urlresolvers import reverse

from core.mixins import LoginPermissionRequiredMixin, update_permissions

from resources.forms import AddResourceFromLibraryForm
from resources.views import mixins as resource_mixins
from party.messages import TENURE_REL_CREATE
from . import mixins
from organization.views import mixins as organization_mixins
from .. import forms
from ..serializers import SpatialUnitGeoJsonSerializer
from .. import messages as error_messages


class LocationsList(LoginPermissionRequiredMixin,
                    mixins.SpatialQuerySetMixin,
                    organization_mixins.ProjectAdminCheckMixin,
                    generic.ListView):
    template_name = 'spatial/location_map.html'
    permission_required = 'spatial.list'
    permission_denied_message = error_messages.SPATIAL_LIST


class LocationsAdd(LoginPermissionRequiredMixin,
                   mixins.SpatialQuerySetMixin,
                   organization_mixins.ProjectAdminCheckMixin,
                   generic.CreateView):
    form_class = forms.LocationForm
    template_name = 'spatial/location_add.html'
    permission_required = update_permissions('spatial.add')
    permission_denied_message = error_messages.SPATIAL_CREATE

    def get_perms_objects(self):
        return [self.get_project()]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        prj = self.get_project()

        kwargs['schema_selectors'] = ()
        if prj.current_questionnaire:
            kwargs['schema_selectors'] = (
                {'name': 'organization',
                 'value': prj.organization,
                 'selector': prj.organization.id},
                {'name': 'project',
                 'value': prj,
                 'selector': prj.id},
                {'name': 'questionnaire',
                 'value': prj.current_questionnaire,
                 'selector': prj.current_questionnaire}
            )

        return kwargs


class LocationDetail(LoginPermissionRequiredMixin,
                     JsonAttrsMixin,
                     mixins.SpatialUnitObjectMixin,
                     organization_mixins.ProjectAdminCheckMixin,
                     resource_mixins.HasUnattachedResourcesMixin,
                     resource_mixins.DetachableResourcesListMixin,
                     generic.DetailView):
    template_name = 'spatial/location_detail.html'
    permission_required = 'spatial.view'
    permission_denied_message = error_messages.SPATIAL_VIEW
    attributes_field = 'attributes'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['relationships'] = self.object.tenurerelationship_set.all()
        return context


class LocationEdit(LoginPermissionRequiredMixin,
                   mixins.SpatialUnitObjectMixin,
                   organization_mixins.ProjectAdminCheckMixin,
                   generic.UpdateView):
    template_name = 'spatial/location_edit.html'
    form_class = forms.LocationForm
    permission_required = update_permissions('spatial.edit')
    permission_denied_message = error_messages.SPATIAL_UPDATE


class LocationDelete(LoginPermissionRequiredMixin,
                     mixins.SpatialUnitObjectMixin,
                     organization_mixins.ProjectAdminCheckMixin,
                     generic.DeleteView):
    template_name = 'spatial/location_delete.html'
    permission_required = update_permissions('spatial.delete')
    permission_denied_message = error_messages.SPATIAL_DELETE

    def get_success_url(self):
        kwargs = self.kwargs
        del kwargs['location']
        return reverse('locations:list', kwargs=self.kwargs)


class LocationResourceAdd(LoginPermissionRequiredMixin,
                          mixins.SpatialUnitResourceMixin,
                          base_generic.edit.FormMixin,
                          organization_mixins.ProjectAdminCheckMixin,
                          generic.DetailView):
    template_name = 'spatial/resources_add.html'
    form_class = AddResourceFromLibraryForm
    permission_required = update_permissions('spatial.resources.add')
    permission_denied_message = error_messages.SPATIAL_ADD_RESOURCE

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)


class LocationResourceNew(LoginPermissionRequiredMixin,
                          mixins.SpatialUnitResourceMixin,
                          organization_mixins.ProjectAdminCheckMixin,
                          resource_mixins.HasUnattachedResourcesMixin,
                          generic.CreateView):
    template_name = 'spatial/resources_new.html'
    permission_required = update_permissions('spatial.resource.add')
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
                            organization_mixins.ProjectAdminCheckMixin,
                            generic.CreateView):
    template_name = 'spatial/relationship_add.html'
    form_class = forms.TenureRelationshipForm
    permission_required = update_permissions('tenure_rel.create')
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

        kwargs['initial'] = {
            'new_entity': not self.get_project().parties.exists(),
        }

        prj = self.get_project()
        kwargs['schema_selectors'] = ()
        if prj.current_questionnaire:
            kwargs['schema_selectors'] = (
                {'name': 'organization',
                 'value': prj.organization,
                 'selector': prj.organization.id},
                {'name': 'project',
                 'value': prj,
                 'selector': prj.id},
                {'name': 'questionnaire',
                 'value': prj.current_questionnaire,
                 'selector': prj.current_questionnaire}
            )

        return kwargs

    def get_success_url(self):
        return (reverse('locations:detail', kwargs=self.kwargs) +
                '#relationships')
