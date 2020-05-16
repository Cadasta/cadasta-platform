import django.views.generic as base_generic
from core.mixins import LoginPermissionRequiredMixin, update_permissions
from core.views import generic
from core.views.mixins import ArchiveMixin
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.http import Http404
from organization.views import mixins as organization_mixins

from . import mixins
from .. import messages as error_messages
from ..exceptions import InvalidGPXFile
from ..forms import AddResourceFromLibraryForm
from ..models import ContentObject, Resource


class ProjectResources(LoginPermissionRequiredMixin,
                       mixins.ProjectResourceMixin,
                       mixins.DetachableResourcesListMixin,
                       organization_mixins.ProjectAdminCheckMixin,
                       generic.ListView):
    template_name = 'resources/project_list.html'
    permission_required = 'resource.list'
    permission_denied_message = error_messages.RESOURCE_LIST

    def filter_archived_resources(self, view, obj):
        if obj.archived:
            return ('resource.view', 'resource.unarchive')
        else:
            return ('resource.view',)

    permission_filter_queryset = filter_archived_resources
    use_resource_library_queryset = True

    def get_resource_list(self):
        return self.get_queryset()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['success_url'] = None
        return context


class ProjectResourcesAdd(LoginPermissionRequiredMixin,
                          mixins.ProjectResourceMixin,
                          base_generic.edit.FormMixin,
                          organization_mixins.ProjectAdminCheckMixin,
                          generic.DetailView):
    template_name = 'resources/project_add_existing.html'
    form_class = AddResourceFromLibraryForm
    permission_required = update_permissions('resource.add')
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
                          organization_mixins.ProjectAdminCheckMixin,
                          generic.CreateView):
    template_name = 'resources/project_add_new.html'
    permission_required = update_permissions('resource.add')
    permission_denied_message = error_messages.RESOURCE_ADD

    def get_perms_objects(self):
        return [self.get_project()]

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except InvalidGPXFile as e:
            error = ValidationError(str(e))
            form = self.get_form()
            form.add_error('file', error)
            return self.form_invalid(form)


class ProjectResourcesDetail(LoginPermissionRequiredMixin,
                             mixins.ResourceObjectMixin,
                             organization_mixins.ProjectAdminCheckMixin,
                             generic.DetailView):
    template_name = 'resources/project_detail.html'
    permission_required = 'resource.view'
    permission_denied_message = error_messages.RESOURCE_VIEW

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # Construct list of objects resource is attached to
        attachments = ContentObject.objects.filter(resource=self.get_object())
        attachment_list = [
            {
                'object': attachment.content_type.get_object_for_this_type(
                    pk=attachment.object_id),
                'id': attachment.id,
            } for attachment in attachments
        ]

        context['attachment_list'] = attachment_list
        context['success_url'] = None
        return context


class ProjectResourcesEdit(LoginPermissionRequiredMixin,
                           mixins.ResourceObjectMixin,
                           organization_mixins.ProjectAdminCheckMixin,
                           generic.UpdateView):
    template_name = 'resources/edit.html'
    permission_required = update_permissions('resource.edit')
    permission_denied_message = error_messages.RESOURCE_EDIT

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['cancel_url'] = self.get_success_url()
        return context


class ResourceArchive(LoginPermissionRequiredMixin,
                      ArchiveMixin,
                      mixins.ResourceObjectMixin,
                      generic.UpdateView):
    do_archive = True
    permission_required = update_permissions('resource.archive')
    permission_denied_message = error_messages.RESOURCE_ARCHIVE

    def get_success_url(self):
        next_url = self.request.GET.get('next', None)
        if next_url:
            return next_url + '#resources'
        if self.request.user.has_perm('resource.unarchive', self.get_object()):
            return reverse('resources:project_detail', kwargs=self.kwargs)
        else:
            kwargs = self.kwargs.copy()
            del kwargs['resource']
            return reverse('resources:project_list', kwargs=kwargs)


class ResourceUnarchive(LoginPermissionRequiredMixin,
                        ArchiveMixin,
                        mixins.ResourceObjectMixin,
                        generic.UpdateView):
    do_archive = False
    permission_required = update_permissions('resource.unarchive')
    permission_denied_message = error_messages.RESOURCE_UNARCHIVE


class ResourceDetach(LoginPermissionRequiredMixin,
                     organization_mixins.ProjectMixin,
                     generic.DeleteView):
    http_method_names = ('post',)
    model = ContentObject
    pk_url_kwarg = 'attachment'
    permission_required = update_permissions('resource.edit')
    permission_denied_message = error_messages.RESOURCE_EDIT

    def get_object(self):
        try:
            return ContentObject.objects.get(
                id=self.kwargs['attachment'],
                resource__id=self.kwargs['resource'],
                resource__project__slug=self.kwargs['project'],
            )
        except ContentObject.DoesNotExist as e:
            raise Http404(e)

    def get_perms_objects(self):
        try:
            return [Resource.objects.get(pk=self.kwargs['resource'])]
        except Resource.DoesNotExist as e:
            raise Http404(e)

    def get_success_url(self):
        next_url = self.request.GET.get('next', None)
        if next_url:
            return next_url + '#resources'
        return reverse(
            'resources:project_list',
            kwargs={
                'organization': self.kwargs['organization'],
                'project': self.kwargs['project'],
            }
        )
