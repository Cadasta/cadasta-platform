from core.views import generic
import django.views.generic as base_generic
from core.views.mixins import ArchiveMixin

from core.mixins import LoginPermissionRequiredMixin

from . import mixins
from organization.views import mixins as organization_mixins
from ..forms import AddResourceFromLibraryForm
from .. import messages as error_messages


class ProjectResources(LoginPermissionRequiredMixin,
                       mixins.ProjectResourceMixin,
                       mixins.ProjectHasResourcesMixin,
                       organization_mixins.ProjectAdminCheckMixin,
                       generic.ListView):
    template_name = 'resources/project_list.html'
    permission_required = 'resource.list'
    permission_denied_message = error_messages.RESOURCE_LIST
    permission_filter_queryset = ('resource.view',)


class ProjectResourcesAdd(LoginPermissionRequiredMixin,
                          mixins.ProjectResourceMixin,
                          base_generic.edit.FormMixin,
                          generic.DetailView):
    template_name = 'resources/project_add_existing.html'
    form_class = AddResourceFromLibraryForm
    permission_required = 'resource.add'
    permission_denied_message = error_messages.RESOURCE_ADD

    def get_object(self):
        return self.get_project()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)


class ProjectResourcesNew(LoginPermissionRequiredMixin,
                          mixins.ProjectResourceMixin,
                          mixins.ProjectHasResourcesMixin,
                          generic.CreateView):
    template_name = 'resources/project_add_new.html'
    permission_required = 'resource.add'
    permission_denied_message = error_messages.RESOURCE_ADD

    def get_perms_objects(self):
        return [self.get_project()]


class ProjectResourcesDetail(LoginPermissionRequiredMixin,
                             mixins.ResourceObjectMixin,
                             generic.DetailView):
    template_name = 'resources/project_detail.html'
    permission_required = 'resource.view'
    permission_denied_message = error_messages.RESOURCE_VIEW

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['object_list'] = self.get_queryset()
        return context


class ProjectResourcesEdit(LoginPermissionRequiredMixin,
                           mixins.ResourceObjectMixin,
                           generic.UpdateView):
    template_name = 'resources/edit.html'
    permission_required = 'resource.edit'
    permission_denied_message = error_messages.RESOURCE_EDIT


class ResourceArchive(LoginPermissionRequiredMixin,
                      ArchiveMixin,
                      mixins.ResourceObjectMixin,
                      generic.UpdateView):
    do_archive = True
    permission_required = 'resource.archive'
    permission_denied_message = error_messages.RESOURCE_ARCHIVE


class ResourceUnarchive(LoginPermissionRequiredMixin,
                        ArchiveMixin,
                        mixins.ResourceObjectMixin,
                        generic.UpdateView):
    do_archive = False
    permission_required = 'resource.unarchive'
    permission_denied_message = error_messages.RESOURCE_UNARCHIVE
