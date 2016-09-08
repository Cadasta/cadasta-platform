from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.http import Http404

from organization.views.mixins import ProjectMixin

from ..models import Resource, ContentObject
from ..serializers import ResourceSerializer
from ..forms import ResourceForm


class ResourceViewMixin:
    form_class = ResourceForm
    serializer_class = ResourceSerializer

    def get_queryset(self):
        if hasattr(self, 'use_resource_library_queryset'):
            return self.get_project().resource_set.all()
        else:
            return self.get_content_object().resources.all()

    def get_model_context(self):
        return {
            'content_object': self.get_content_object(),
            'contributor': self.request.user
        }

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context.update(self.get_model_context())
        return context

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs.update(self.get_model_context())
        return form_kwargs

    def get_content_object(self):
        raise NotImplementedError('You need to implement get_content_object.')


class ProjectResourceMixin(ProjectMixin, ResourceViewMixin):
    def get_content_object(self):
        return self.get_project()

    def get_model_context(self):
        context = super().get_model_context()
        context['project_id'] = self.get_project().id
        return context

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['object'] = self.get_project()
        return context

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


class ResourceObjectMixin(ProjectResourceMixin):
    def get_object(self):
        if hasattr(self, 'resource'):
            return self.resource
        try:
            resource = Resource.objects.get(
                project__organization__slug=self.kwargs['organization'],
                project__slug=self.kwargs['project'],
                id=self.kwargs['resource']
            )
        except Resource.DoesNotExist as e:
            raise Http404(e)
        if (
            resource.archived and
            not self.request.user.has_perm('resource.unarchive', resource)
        ):
            raise Http404(Resource.DoesNotExist)
        else:
            self.resource = resource
            return resource

    def get_perms_objects(self):
        return [self.get_object()]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        resource = self.get_object()
        user = self.request.user
        context['resource'] = resource
        context['can_edit'] = user.has_perm('resource.edit', resource)
        context['can_archive'] = user.has_perm('resource.archive', resource)
        return context

    def get_success_url(self):
        next_url = self.request.GET.get('next', None)
        if next_url:
            return next_url + '#resources'

        project = self.get_project()
        return reverse(
            'resources:project_detail',
            kwargs={
                'organization': project.organization.slug,
                'project': project.slug,
                'resource': self.get_object().id,
            }
        )


class HasUnattachedResourcesMixin(ProjectMixin):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # Determine the object that can have resources
        if hasattr(self, 'get_content_object'):
            # This is for views for uploading a new resource
            # or the ProjectResources view
            object = self.get_content_object()
        elif hasattr(self, 'object'):
            # This is for views that list entity resources
            object = self.object

        project_resource_set_count = self.get_project().resource_set.filter(
            archived=False).count()
        if (
            project_resource_set_count > 0 and
            project_resource_set_count != object.resources.count()
        ):
            context['has_unattached_resources'] = True

        return context


class DetachableResourcesListMixin(ProjectMixin):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # Get current object whose resources is being listed
        if hasattr(self, 'get_object'):
            content_object = self.get_object()
        else:
            content_object = self.get_project()
        model_type = ContentType.objects.get_for_model(content_object)

        # Get the list of resources to be displayed
        if hasattr(self, 'get_resource_list'):
            resource_list = self.get_resource_list()
        else:
            resource_list = content_object.resources.all()

        # Get attachment IDs as a dictionary keyed on resource IDs
        attachments = ContentObject.objects.filter(
            content_type__pk=model_type.id,
            object_id=content_object.id,
        )
        attachment_id_dict = {x.resource.id: x.id for x in attachments}

        # Update resource list with attachment IDs referring to the object
        for resource in resource_list:
            attachment_id = attachment_id_dict.get(resource.id, None)
            setattr(resource, 'attachment_id', attachment_id)

        context['resource_list'] = resource_list
        return context
