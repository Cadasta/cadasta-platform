from jsonattrs.mixins import JsonAttrsMixin
from core.views import generic
from django.core.urlresolvers import reverse
import django.views.generic as base_generic
from core.mixins import LoginPermissionRequiredMixin, update_permissions
from organization.views import mixins as organization_mixins
from resources.forms import AddResourceFromLibraryForm
from resources.views import mixins as resource_mixins
from . import mixins
from .. import forms
from .. import messages as error_messages


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
