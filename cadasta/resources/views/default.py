from django.core.urlresolvers import reverse
from django.http import Http404
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType
from core.views import generic
import django.views.generic as base_generic
from core.views.mixins import ArchiveMixin

from core.mixins import LoginPermissionRequiredMixin

from ..models import Resource, ContentObject
from . import mixins
from organization.views import mixins as organization_mixins
from ..forms import AddResourceFromLibraryForm
from .. import messages as error_messages
from organization.models import Project
from spatial.models import SpatialUnit
from party.models import Party


class ProjectResources(LoginPermissionRequiredMixin,
                       mixins.ProjectResourceMixin,
                       mixins.HasUnattachedResourcesMixin,
                       mixins.DetachableResourcesListMixin,
                       organization_mixins.ProjectAdminCheckMixin,
                       generic.ListView):
    template_name = 'resources/project_list.html'
    permission_required = 'resource.list'
    permission_denied_message = error_messages.RESOURCE_LIST
    permission_filter_queryset = ('resource.view',)
    use_resource_library_queryset = True

    def get_resource_list(self):
        return self.get_queryset()


class ProjectResourcesAdd(LoginPermissionRequiredMixin,
                          mixins.ProjectResourceMixin,
                          base_generic.edit.FormMixin,
                          organization_mixins.ProjectAdminCheckMixin,
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
                          mixins.HasUnattachedResourcesMixin,
                          organization_mixins.ProjectAdminCheckMixin,
                          generic.CreateView):
    template_name = 'resources/project_add_new.html'
    permission_required = 'resource.add'
    permission_denied_message = error_messages.RESOURCE_ADD

    def get_perms_objects(self):
        return [self.get_project()]


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
        attachment_list = []
        project = self.get_project()
        attachments = ContentObject.objects.filter(resource=self.get_object())
        type_lookup = ContentType.objects.get_for_model
        for attachment in attachments:
            content_type = attachment.content_type
            object = content_type.get_object_for_this_type(
                pk=attachment.object_id)

            if content_type == type_lookup(Project):
                url = reverse(
                    'organization:project-dashboard',
                    kwargs={
                        'organization': project.organization.slug,
                        'project': project.slug,
                    },
                )
                class_name = _("Project")
                name = project.name

            elif content_type == type_lookup(SpatialUnit):
                url = reverse(
                    'locations:detail',
                    kwargs={
                        'organization': project.organization.slug,
                        'project': project.slug,
                        'location': attachment.object_id,
                    },
                )
                class_name = _("Location")
                name = object.get_type_display()

            elif content_type == type_lookup(Party):
                url = reverse(
                    'parties:detail',
                    kwargs={
                        'organization': project.organization.slug,
                        'project': project.slug,
                        'party': attachment.object_id,
                    },
                )
                class_name = _("Party")
                name = object.name

            else:  # content_type == type_lookup(TenureRelationship):
                url = reverse(
                    'parties:relationship_detail',
                    kwargs={
                        'organization': project.organization.slug,
                        'project': project.slug,
                        'relationship': attachment.object_id,
                    },
                )
                class_name = _("Relationship")
                name = "<{party}> {type} <{su}>".format(
                    party=object.party.name,
                    su=object.spatial_unit.get_type_display(),
                    type=object.tenure_type.label,
                )

            # TODO: There should probably be an actual else case here that
            # should be treated as an exception because it means that the
            # resource is attached to an unexpected object

            attachment_list.append({
                'url': url,
                'class': class_name,
                'name': name,
                'id': attachment.id,
            })

        context['attachment_list'] = attachment_list
        return context


class ProjectResourcesEdit(LoginPermissionRequiredMixin,
                           mixins.ResourceObjectMixin,
                           organization_mixins.ProjectAdminCheckMixin,
                           generic.UpdateView):
    template_name = 'resources/edit.html'
    permission_required = 'resource.edit'
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
    permission_required = 'resource.archive'
    permission_denied_message = error_messages.RESOURCE_ARCHIVE


class ResourceUnarchive(LoginPermissionRequiredMixin,
                        ArchiveMixin,
                        mixins.ResourceObjectMixin,
                        generic.UpdateView):
    do_archive = False
    permission_required = 'resource.unarchive'
    permission_denied_message = error_messages.RESOURCE_UNARCHIVE


class ResourceDetach(LoginPermissionRequiredMixin,
                     organization_mixins.ProjectMixin,
                     generic.DeleteView):
    http_method_names = ('post',)
    model = ContentObject
    pk_url_kwarg = 'attachment'
    permission_required = 'resource.edit'
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

        project = self.get_project()
        return reverse(
            'resources:project_list',
            kwargs={
                'organization': project.organization.slug,
                'project': project.slug,
            }
        )
