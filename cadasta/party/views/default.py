from core.views import generic
import django.views.generic as base_generic
from django.core.urlresolvers import reverse
from jsonattrs.mixins import JsonAttrsMixin, template_xlang_labels
from core.mixins import LoginPermissionRequiredMixin, update_permissions

from organization.views import mixins as organization_mixins
from resources.forms import AddResourceFromLibraryForm
from resources.views import mixins as resource_mixins
from questionnaires.models import Question, QuestionOption
from . import mixins
from .. import forms
from .. import messages as error_messages


class PartiesList(LoginPermissionRequiredMixin,
                  organization_mixins.ProjectMixin,
                  organization_mixins.ProjectAdminCheckMixin,
                  generic.TemplateView):
    template_name = 'party/party_list.html'
    permission_required = 'party.list'
    permission_denied_message = error_messages.PARTY_LIST

    def get_perms_objects(self):
        return [self.get_project()]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['object'] = self.get_project()
        return context


class PartiesAdd(LoginPermissionRequiredMixin,
                 mixins.PartyQuerySetMixin,
                 generic.CreateView):
    form_class = forms.PartyForm
    template_name = 'party/party_add.html'
    permission_required = update_permissions('party.create')
    permission_denied_message = error_messages.PARTY_CREATE

    def get_perms_objects(self):
        return [self.get_project()]

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['project'] = self.get_project()
        return kwargs

    def get_success_url(self):
        return reverse('parties:list', kwargs=self.kwargs)


class PartiesDetail(LoginPermissionRequiredMixin,
                    JsonAttrsMixin,
                    mixins.PartyObjectMixin,
                    organization_mixins.ProjectAdminCheckMixin,
                    resource_mixins.HasUnattachedResourcesMixin,
                    resource_mixins.DetachableResourcesListMixin,
                    generic.DetailView):
    template_name = 'party/party_detail.html'
    permission_required = 'party.view'
    permission_denied_message = error_messages.PARTY_VIEW
    attributes_field = 'attributes'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['relationships'] = self.object.tenurerelationship_set.all(
        ).select_related('spatial_unit').defer('spatial_unit__attributes')

        project = context['object']
        if project.current_questionnaire:
            try:
                name = Question.objects.get(
                    name='party_name',
                    questionnaire_id=project.current_questionnaire)
                context['name_labels'] = template_xlang_labels(name.label_xlat)
            except Question.DoesNotExist:
                pass

            try:
                party_type = Question.objects.get(
                    name='party_type',
                    questionnaire_id=project.current_questionnaire)
                context['type_labels'] = template_xlang_labels(
                    party_type.label_xlat)
            except Question.DoesNotExist:
                pass
            else:
                try:
                    option = QuestionOption.objects.get(
                        question=party_type,
                        name=context['party'].type)
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
            except Question.DoesNotExist:
                tenure_opts = None

            try:
                location_type = Question.objects.get(
                    name='location_type',
                    questionnaire_id=project.current_questionnaire)
                location_opts = QuestionOption.objects.filter(
                    question=location_type)
                location_opts = dict(
                    location_opts.values_list('name', 'label_xlat'))
            except Question.DoesNotExist:
                location_opts = None

            for rel in context['relationships']:
                if tenure_opts:
                    rel.type_labels = template_xlang_labels(
                        tenure_opts.get(rel.tenure_type))
                if location_opts:
                    rel.location_labels = template_xlang_labels(
                        location_opts.get(rel.spatial_unit.type))

        return context


class PartiesEdit(LoginPermissionRequiredMixin,
                  JsonAttrsMixin,
                  mixins.PartyObjectMixin,
                  organization_mixins.ProjectAdminCheckMixin,
                  generic.UpdateView):
    template_name = 'party/party_edit.html'
    form_class = forms.PartyForm
    permission_required = update_permissions('party.update')
    permission_denied_message = error_messages.PARTY_UPDATE
    attributes_field = 'attributes'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        project = context['object']
        if project.current_questionnaire:
            try:
                party_type = Question.objects.get(
                    name='party_type',
                    questionnaire_id=project.current_questionnaire)
                option = QuestionOption.objects.get(question=party_type,
                                                    name=context['party'].type)
                context['type_choice_labels'] = template_xlang_labels(
                    option.label_xlat)
            except Question.DoesNotExist:
                pass

        return context


class PartiesDelete(LoginPermissionRequiredMixin,
                    mixins.PartyObjectMixin,
                    organization_mixins.ProjectAdminCheckMixin,
                    generic.DeleteView):
    template_name = 'party/party_delete.html'
    permission_required = update_permissions('party.delete')
    permission_denied_message = error_messages.PARTY_DELETE

    def get_success_url(self):
        kwargs = self.kwargs
        del kwargs['party']
        return reverse('parties:list', kwargs=self.kwargs)


class PartyResourcesAdd(LoginPermissionRequiredMixin,
                        mixins.PartyResourceMixin,
                        organization_mixins.ProjectAdminCheckMixin,
                        base_generic.edit.FormMixin,
                        generic.DetailView):
    template_name = 'party/resources_add.html'
    form_class = AddResourceFromLibraryForm
    permission_required = update_permissions('party.resources.add')
    permission_denied_message = error_messages.PARTY_RESOURCES_ADD

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)


class PartyResourcesNew(LoginPermissionRequiredMixin,
                        mixins.PartyResourceMixin,
                        organization_mixins.ProjectAdminCheckMixin,
                        resource_mixins.HasUnattachedResourcesMixin,
                        generic.CreateView):
    template_name = 'party/resources_new.html'
    permission_required = update_permissions('party.resources.add')
    permission_denied_message = error_messages.PARTY_RESOURCES_ADD


class PartyRelationshipDetail(LoginPermissionRequiredMixin,
                              JsonAttrsMixin,
                              mixins.PartyRelationshipObjectMixin,
                              organization_mixins.ProjectAdminCheckMixin,
                              resource_mixins.HasUnattachedResourcesMixin,
                              resource_mixins.DetachableResourcesListMixin,
                              generic.DetailView):
    template_name = 'party/relationship_detail.html'
    permission_required = 'tenure_rel.view'
    permission_denied_message = error_messages.TENURE_REL_VIEW
    attributes_field = 'attributes'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        project = context['object']
        if project.current_questionnaire:
            try:
                tenure_type = Question.objects.get(
                    name='tenure_type',
                    questionnaire_id=project.current_questionnaire)
                context['type_labels'] = template_xlang_labels(
                    tenure_type.label_xlat)
            except Question.DoesNotExist:
                pass
            else:
                try:
                    option = QuestionOption.objects.get(
                        question=tenure_type,
                        name=context['relationship'].tenure_type)
                    context['type_choice_labels'] = template_xlang_labels(
                        option.label_xlat)
                except QuestionOption.DoesNotExist:
                    pass

        return context


class PartyRelationshipEdit(LoginPermissionRequiredMixin,
                            mixins.PartyRelationshipObjectMixin,
                            organization_mixins.ProjectAdminCheckMixin,
                            generic.UpdateView):
    template_name = 'party/relationship_edit.html'
    form_class = forms.TenureRelationshipEditForm
    permission_required = update_permissions('tenure_rel.update')
    permission_denied_message = error_messages.TENURE_REL_UPDATE

    def get_success_url(self):
        return reverse('parties:relationship_detail', kwargs=self.kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs


class PartyRelationshipDelete(LoginPermissionRequiredMixin,
                              mixins.PartyRelationshipObjectMixin,
                              organization_mixins.ProjectAdminCheckMixin,
                              generic.DeleteView):
    template_name = 'party/relationship_delete.html'
    permission_required = update_permissions('tenure_rel.delete')
    permission_denied_message = error_messages.TENURE_REL_DELETE

    def get_success_url(self):
        kwargs = self.kwargs
        del kwargs['relationship']
        return reverse('locations:list', kwargs=self.kwargs)


class PartyRelationshipResourceNew(LoginPermissionRequiredMixin,
                                   mixins.PartyRelationshipResourceMixin,
                                   organization_mixins.ProjectAdminCheckMixin,
                                   resource_mixins.HasUnattachedResourcesMixin,
                                   generic.CreateView):
    template_name = 'party/relationship_resources_new.html'
    permission_required = update_permissions('tenure_rel.resources.add')
    permission_denied_message = error_messages.TENURE_REL_RESOURCES_ADD


class PartyRelationshipResourceAdd(LoginPermissionRequiredMixin,
                                   mixins.PartyRelationshipResourceMixin,
                                   organization_mixins.ProjectAdminCheckMixin,
                                   base_generic.edit.FormMixin,
                                   generic.DetailView):
    template_name = 'party/relationship_resources_add.html'
    form_class = AddResourceFromLibraryForm
    permission_required = update_permissions('tenure_rel.resources.add')
    permission_denied_message = error_messages.TENURE_REL_RESOURCES_ADD

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)
