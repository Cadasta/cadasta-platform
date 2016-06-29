from django.views import generic
from django.core.urlresolvers import reverse
from core.mixins import LoginPermissionRequiredMixin

from resources.forms import AddResourceFromLibraryForm
from . import mixins
from .. import forms
from .. import messages as error_messages


class PartiesList(LoginPermissionRequiredMixin,
                  mixins.PartyQuerySetMixin,
                  generic.ListView):
    template_name = 'party/party_list.html'
    permission_required = 'party.list'
    permission_denied_message = error_messages.PARTY_LIST
    permission_filter_queryset = ('party.view',)


class PartiesAdd(LoginPermissionRequiredMixin,
                 mixins.PartyQuerySetMixin,
                 generic.CreateView):
    form_class = forms.PartyForm
    template_name = 'party/party_add.html'
    permission_required = 'party.create'
    permission_denied_message = error_messages.PARTY_CREATE

    def get_perms_objects(self):
        return [self.get_project()]


class PartiesDetail(LoginPermissionRequiredMixin,
                    mixins.PartyObjectMixin,
                    generic.DetailView):
    template_name = 'party/party_detail.html'
    permission_required = 'party.view'
    permission_denied_message = error_messages.PARTY_VIEW


class PartiesEdit(LoginPermissionRequiredMixin,
                  mixins.PartyObjectMixin,
                  generic.UpdateView):
    template_name = 'party/party_edit.html'
    form_class = forms.PartyForm
    permission_required = 'party.update'
    permission_denied_message = error_messages.PARTY_UPDATE


class PartiesDelete(LoginPermissionRequiredMixin,
                    mixins.PartyObjectMixin,
                    generic.DeleteView):
    template_name = 'party/party_delete.html'
    permission_required = 'party.delete'
    permission_denied_message = error_messages.PARTY_DELETE

    def get_success_url(self):
        kwargs = self.kwargs
        del kwargs['party']
        return reverse('locations:list', kwargs=self.kwargs)


class PartyResourcesAdd(LoginPermissionRequiredMixin,
                        mixins.PartyResourceMixin,
                        generic.edit.FormMixin,
                        generic.DetailView):
    template_name = 'party/resources_add.html'
    form_class = AddResourceFromLibraryForm
    permission_required = 'party.resources.add'
    permission_denied_message = error_messages.PARTY_RESOURCES_ADD

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)


class PartyResourcesNew(LoginPermissionRequiredMixin,
                        mixins.PartyResourceMixin,
                        generic.CreateView):
    template_name = 'party/resources_new.html'
    permission_required = 'party.resources.add'
    permission_denied_message = error_messages.PARTY_RESOURCES_ADD


class PartyRelationshipDetail(LoginPermissionRequiredMixin,
                              mixins.PartyRelationshipObjectMixin,
                              generic.DetailView):
    template_name = 'party/relationship_detail.html'
    permission_required = 'tenure_rel.view'
    permission_denied_message = error_messages.TENURE_REL_VIEW


class PartyRelationshipEdit(LoginPermissionRequiredMixin,
                            mixins.PartyRelationshipObjectMixin,
                            generic.UpdateView):
    template_name = 'party/relationship_edit.html'
    form_class = forms.TenureRelationshipEditForm
    permission_required = 'tenure_rel.update'
    permission_denied_message = error_messages.TENURE_REL_UPDATE

    def get_success_url(self):
        return reverse('parties:relationship_detail', kwargs=self.kwargs)


class PartyRelationshipDelete(LoginPermissionRequiredMixin,
                              mixins.PartyRelationshipObjectMixin,
                              generic.DeleteView):
    template_name = 'party/relationship_delete.html'
    permission_required = 'tenure_rel.delete'
    permission_denied_message = error_messages.TENURE_REL_DELETE

    def get_success_url(self):
        kwargs = self.kwargs
        del kwargs['relationship']
        return reverse('locations:list', kwargs=self.kwargs)


class PartyRelationshipResourceNew(LoginPermissionRequiredMixin,
                                   mixins.PartyRelationshipResourceMixin,
                                   generic.CreateView):
    template_name = 'party/relationship_resources_new.html'
    permission_required = 'tenure_rel.resources.add'
    permission_denied_message = error_messages.TENURE_REL_RESOURCES_ADD


class PartyRelationshipResourceAdd(LoginPermissionRequiredMixin,
                                   mixins.PartyRelationshipResourceMixin,
                                   generic.edit.FormMixin,
                                   generic.DetailView):
    template_name = 'party/relationship_resources_add.html'
    form_class = AddResourceFromLibraryForm
    permission_required = 'tenure_rel.resources.add'
    permission_denied_message = error_messages.TENURE_REL_RESOURCES_ADD

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)
