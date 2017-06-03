import math
import json

import django.views.generic as base_generic
from core import mixins as core_mixins
from core.views import generic
from django.contrib.gis.geos import Polygon
from django.core.urlresolvers import reverse
from django.http import HttpResponse
# from rest_framework_gis.pagination import GeoJsonPagination
from jsonattrs.mixins import JsonAttrsMixin, template_xlang_labels
from organization.views import mixins as organization_mixins
from party.messages import TENURE_REL_CREATE
from questionnaires.models import Question, QuestionOption
from resources.forms import AddResourceFromLibraryForm
from resources.views import mixins as resource_mixins
from rest_framework import generics
from tutelary.mixins import APIPermissionRequiredMixin

from . import mixins
from .. import messages as error_messages
from .. import forms, serializers


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int(
        (1.0 - math.log(math.tan(lat_rad) +
                        (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return [xtile, ytile]


def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return [lon_deg, lat_deg]


class SpatialUnitTiles(APIPermissionRequiredMixin,
                       mixins.SpatialQuerySetMixin,
                       generics.ListAPIView):

    serializer_class = serializers.SpatialUnitGeoJsonSerializer

    def get_actions(self, request):
        if self.get_project().archived:
            return ['project.view_archived', 'spatial.list']
        if self.get_project().public():
            return ['project.view', 'spatial.list']
        else:
            return ['project.view_private', 'spatial.list']

    permission_required = {
        'GET': get_actions
    }

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        x = int(self.kwargs['x'])
        y = int(self.kwargs['y'])
        zoom = int(self.kwargs['z'])

        bbox = num2deg(xtile=x, ytile=y, zoom=zoom)
        bbox.extend(num2deg(xtile=x + 1, ytile=y + 1, zoom=zoom))
        bbox = Polygon.from_bbox(bbox)
        final_queryset = queryset.filter(
            geometry__intersects=bbox).exclude(
            id=self.request.GET.get('exclude'))

        return final_queryset

    def get_perms_objects(self):
        return [self.get_project()]


class LocationDetail(core_mixins.LoginPermissionRequiredMixin,
                     core_mixins.SpatialUnitCoords,
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
        context['relationships'] = self.object.tenurerelationship_set.all(
        ).select_related('party').defer('party__attributes')

        project = context['object']
        if project.current_questionnaire:
            try:
                question = Question.objects.get(
                    name='location_type',
                    questionnaire_id=project.current_questionnaire)
                context['type_labels'] = template_xlang_labels(
                    question.label_xlat)
            except Question.DoesNotExist:
                pass
            else:
                try:
                    option = QuestionOption.objects.get(
                        question=question,
                        name=context['location'].type)
                    context['type_choice_labels'] = template_xlang_labels(
                        option.label_xlat)
                except QuestionOption.DoesNotExist:
                    pass

            try:
                tenure_type = Question.objects.get(
                    name='tenure_type',
                    questionnaire_id=project.current_questionnaire)
                tenure_opts = QuestionOption.objects.filter(
                    question=tenure_type)
                tenure_opts = dict(tenure_opts.values_list(
                    'name', 'label_xlat'))

                for rel in context['relationships']:
                    rel.type_labels = template_xlang_labels(
                        tenure_opts.get(rel.tenure_type))
            except Question.DoesNotExist:
                pass

        location = context['location']
        user = self.request.user
        context['is_allowed_edit_location'] = user.has_perm('spatial.update',
                                                            location)
        context['is_allowed_delete_location'] = user.has_perm('spatial.delete',
                                                              location)

        return context


class LocationsAdd(core_mixins.LoginPermissionRequiredMixin,
                   mixins.SpatialQuerySetMixin,
                   core_mixins.FormErrorMixin,
                   organization_mixins.ProjectAdminCheckMixin,
                   generic.CreateView):
    form_class = forms.LocationForm
    template_name = 'spatial/location_add.html'
    permission_required = core_mixins.update_permissions('spatial.add')
    permission_denied_message = error_messages.SPATIAL_CREATE

    def get(self, request, *args, **kwargs):
        referrer = request.META.get('HTTP_REFERER', None)
        if referrer:
            current_url = reverse('organization:project-dashboard',
                                  kwargs=self.kwargs)
            if current_url not in referrer:
                request.session['cancel_add_location_url'] = referrer
        else:
            # In case the browser does not send any referrer
            request.session['cancel_add_location_url'] = (reverse(
                'organization:project-dashboard', kwargs=self.kwargs) +
                '#/overview/')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        project = self.get_project()
        cancel_url = self.request.session.get(
            'cancel_add_location_url', None)
        context['submit_url'] = reverse(
            'async:spatial:add',
            kwargs={
                'organization': project.organization.slug,
                'project': project.slug
            })
        context['cancel_url'] = cancel_url or (reverse(
            'organization:project-dashboard', kwargs=self.kwargs) +
            '#/overview/')
        return context

    def get_perms_objects(self):
        return [self.get_project()]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs

    def form_valid(self, form):
        """If the form is valid, redirect to the supplied URL."""
        self.object = form.save()
        post_data = {'new_location_id': self.object.id}
        return HttpResponse(
            json.dumps(post_data),
            content_type="application/json")


class LocationEdit(core_mixins.LoginPermissionRequiredMixin,
                   core_mixins.SpatialUnitCoords,
                   mixins.SpatialUnitObjectMixin,
                   core_mixins.FormErrorMixin,
                   organization_mixins.ProjectAdminCheckMixin,
                   generic.UpdateView):
    template_name = 'spatial/location_edit.html'
    form_class = forms.LocationForm
    permission_required = core_mixins.update_permissions('spatial.edit')
    permission_denied_message = error_messages.SPATIAL_UPDATE

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        location = context['location']
        context['submit_url'] = reverse(
            'async:spatial:edit',
            kwargs={
                'organization': location.project.organization.slug,
                'project': location.project.slug,
                'location': location.id
            })
        context['cancel_url'] = (
            '#/records/location/{}/'.format(location.id))

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs


class LocationDelete(core_mixins.LoginPermissionRequiredMixin,
                     core_mixins.SpatialUnitCoords,
                     mixins.SpatialUnitObjectMixin,
                     organization_mixins.ProjectAdminCheckMixin,
                     generic.DeleteView):
    template_name = 'spatial/location_delete.html'
    permission_required = core_mixins.update_permissions('spatial.delete')
    permission_denied_message = error_messages.SPATIAL_DELETE

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        location = context['location']
        context['cancel_url'] = (
            '#/records/location/{}/'.format(location.id))
        context['submit_url'] = reverse('async:spatial:delete', kwargs={
            'organization': location.project.organization.slug,
            'project': location.project.slug,
            'location': location.id
        })
        return context

    def get_success_url(self):
        kwargs = self.kwargs
        del kwargs['location']
        return reverse('organization:project-dashboard', kwargs=self.kwargs)


class LocationResourceAdd(core_mixins.LoginPermissionRequiredMixin,
                          core_mixins.SpatialUnitCoords,
                          mixins.SpatialUnitResourceMixin,
                          base_generic.edit.FormMixin,
                          organization_mixins.ProjectAdminCheckMixin,
                          generic.DetailView):
    template_name = 'spatial/resources_add.html'
    form_class = AddResourceFromLibraryForm
    permission_required = core_mixins.update_permissions(
        'spatial.resources.add')
    permission_denied_message = error_messages.SPATIAL_ADD_RESOURCE

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        location = context['location']
        context['cancel_url'] = (
            '#/records/location/{}/?tab=resources'.format(location.id))
        context['upload_url'] = ("#/records/location/{}/resources/new/".format(
                                 location.id))
        context['submit_url'] = reverse(
            'async:spatial:resource_add',
            kwargs={
                'organization': location.project.organization.slug,
                'project': location.project.slug,
                'location': location.id
            })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)


class LocationResourceNew(core_mixins.LoginPermissionRequiredMixin,
                          core_mixins.SpatialUnitCoords,
                          core_mixins.FormErrorMixin,
                          mixins.SpatialUnitResourceMixin,
                          organization_mixins.ProjectAdminCheckMixin,
                          resource_mixins.HasUnattachedResourcesMixin,
                          generic.CreateView):
    template_name = 'spatial/resources_new.html'
    permission_required = core_mixins.update_permissions(
        'spatial.resources.add')
    permission_denied_message = error_messages.SPATIAL_ADD_RESOURCE

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        location = context['location']
        context['cancel_url'] = '#/records/location/{}/?tab=resources'.format(
                                location.id)
        context['add_lib_url'] = (
            "#/records/location/{}/resources/add/".format(
                location.id))

        context['submit_url'] = reverse(
            'async:spatial:resource_new',
            kwargs={
                'organization': location.project.organization.slug,
                'project': location.project.slug,
                'location': location.id
            })
        return context


class TenureRelationshipAdd(core_mixins.LoginPermissionRequiredMixin,
                            core_mixins.SpatialUnitCoords,
                            core_mixins.FormErrorMixin,
                            mixins.SpatialUnitRelationshipMixin,
                            organization_mixins.ProjectAdminCheckMixin,
                            generic.CreateView):
    template_name = 'spatial/relationship_add.html'
    form_class = forms.TenureRelationshipForm
    permission_required = core_mixins.update_permissions('tenure_rel.create')
    permission_denied_message = TENURE_REL_CREATE

    def get_perms_objects(self):
        return [self.get_project()]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {
            'new_entity': not self.get_project().parties.exists(),
        }
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        location = context['location']
        context['submit_url'] = reverse(
            'async:spatial:relationship_add',
            kwargs={
                'organization': location.project.organization.slug,
                'project': location.project.slug,
                'location': location.id
            })
        context['cancel_url'] = (
            '#/records/location/{}/?tab=relationships'.format(
                self.kwargs['location']))
        return context

    def get_success_url(self):
        success_url = (reverse('organization:project-dashboard', kwargs={
            'organization': self.kwargs['organization'],
            'project': self.kwargs['project']
        }) + '#/records/location/{}/?tab=relationships'.format(
            self.kwargs['location']))
        return success_url
