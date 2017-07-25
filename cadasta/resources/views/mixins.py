from django.core.urlresolvers import reverse
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from organization.views.mixins import ProjectMixin

from ..forms import ResourceForm
from ..models import Resource, ContentObject
from ..serializers import ReadOnlyResourceSerializer, ResourceSerializer


class ResourceViewMixin:
    form_class = ResourceForm
    serializer_class = ResourceSerializer

    def get_queryset(self):
        if hasattr(self, 'use_resource_library_queryset'):
            return self.get_project().resource_set.all().select_related(
                'contributor')
        else:
            return self.get_content_object().resources.all().select_related(
                'contributor')

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

    def detach_resource(self, object_id):
        content_object = ContentObject.objects.get(
                object_id=object_id,
                resource__id=self.kwargs['resource'],
                resource__project__slug=self.kwargs['project'],
            )
        content_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        return reverse('resources:project_list', kwargs=self.kwargs)


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
        return reverse('resources:project_detail', kwargs=self.kwargs)


class HasUnattachedResourcesMixin(ProjectMixin):
    def get_content_object(self):
        return self.get_object()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        obj = self.get_content_object()

        project_resource_set_count = self.get_project().resource_set.filter(
            archived=False).count()
        if (
            project_resource_set_count > 0 and
            project_resource_set_count != obj.resources.count()
        ):
            context['has_unattached_resources'] = True

        return context


class SpatialResourceViewMixin():
    serializer_class = ReadOnlyResourceSerializer

    def get_queryset(self):
        # only return unarchived, attached Resources which have
        # associated spatial resources
        project = self.get_content_object()
        return Resource.objects.filter(
            project=project.id, archived=False).exclude(
                content_objects=None).exclude(spatial_resources=None)


class ProjectSpatialResourceMixin(ProjectMixin, SpatialResourceViewMixin):
    def get_content_object(self):
        return self.get_project()
