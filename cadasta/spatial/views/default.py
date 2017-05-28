import django.views.generic as base_generic
from core.mixins import LoginPermissionRequiredMixin, update_permissions
from core.views import generic
from django.core.urlresolvers import reverse
from jsonattrs.mixins import JsonAttrsMixin, template_xlang_labels
from organization.views import mixins as organization_mixins
from party.messages import TENURE_REL_CREATE
from resources.forms import AddResourceFromLibraryForm
from resources.views import mixins as resource_mixins
from questionnaires.models import Question, QuestionOption

from . import mixins
from .. import messages as error_messages
from .. import forms


class LocationsList(LoginPermissionRequiredMixin,
                    mixins.SpatialQuerySetMixin,
                    organization_mixins.ProjectAdminCheckMixin,
                    generic.ListView):
    template_name = 'spatial/location_map.html'
    permission_required = 'spatial.list'
    permission_denied_message = error_messages.SPATIAL_LIST

    def get_perms_objects(self):
        return [self.get_project()]


class LocationsAdd(LoginPermissionRequiredMixin,
                   mixins.SpatialQuerySetMixin,
                   organization_mixins.ProjectAdminCheckMixin,
                   generic.CreateView):
    form_class = forms.LocationForm
    template_name = 'spatial/location_add.html'
    permission_required = update_permissions('spatial.add')
    permission_denied_message = error_messages.SPATIAL_CREATE

    def get(self, request, *args, **kwargs):
        referrer = request.META.get('HTTP_REFERER', None)
        if referrer:
            current_url = reverse('locations:add', kwargs=self.kwargs)
            if current_url not in referrer:
                request.session['cancel_add_location_url'] = referrer
        else:
            # In case the browser does not send any referrer
            request.session['cancel_add_location_url'] = reverse(
                'organization:project-dashboard', kwargs=self.kwargs)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        cancel_url = self.request.session.get('cancel_add_location_url', None)
        context['cancel_url'] = cancel_url or reverse(
            'organization:project-dashboard', kwargs=self.kwargs)
        return context

    def get_perms_objects(self):
        return [self.get_project()]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.get_project()
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
        context['area'] = location.area
        user = self.request.user
        context['is_allowed_edit_location'] = user.has_perm('spatial.update',
                                                            location)
        context['is_allowed_delete_location'] = user.has_perm('spatial.delete',
                                                              location)

        return context


class LocationEdit(LoginPermissionRequiredMixin,
                   mixins.SpatialUnitObjectMixin,
                   organization_mixins.ProjectAdminCheckMixin,
                   generic.UpdateView):
    template_name = 'spatial/location_edit.html'
    form_class = forms.LocationForm
    permission_required = update_permissions('spatial.edit')
    permission_denied_message = error_messages.SPATIAL_UPDATE

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs


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
    permission_required = update_permissions('spatial.resources.add')
    permission_denied_message = error_messages.SPATIAL_ADD_RESOURCE


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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {
            'new_entity': not self.get_project().parties.exists(),
        }
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        return context

    def get_success_url(self):
        return (reverse('locations:detail', kwargs=self.kwargs) +
                '#relationships')
