from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.apps import apps
from tutelary.mixins import APIPermissionRequiredMixin
from rest_framework import generics
from rest_framework.response import Response
from organization.views.mixins import ProjectMixin
from core.views.mixins import SuperUserCheckMixin, AsyncList
from ..models import ContentObject


class ResourcesView(APIPermissionRequiredMixin,
                    SuperUserCheckMixin,
                    AsyncList,
                    ProjectMixin,
                    generics.ListAPIView):
    sort_columns = ('name', 'mime_type', 'contributor__username',
                    'last_updated')
    content_object = 'organization.Project'
    use_resource_library_queryset = True

    def get_actions(self, request):
        if self.get_project().archived:
            return ['project.view_archived', 'resource.list']
        if self.get_project().public():
            return ['project.view', 'resource.list']
        else:
            return ['project.view_private', 'resource.list']

    permission_required = {
        'GET': get_actions
    }

    def get_perms_objects(self):
        return [self.get_project()]

    def get_content_object(self):
        if self.content_object == 'organization.Project':
            return self.get_project()
        else:
            return get_object_or_404(
                apps.get_model(*self.content_object.split('.')),
                project__organization__slug=self.kwargs['organization'],
                project__slug=self.kwargs['project'],
                id=self.kwargs['object_id']
            )

    def build_search_query(self, term):
        return (Q(name__contains=term) |
                Q(original_file__contains=term) |
                Q(mime_type__contains=term) |
                Q(contributor__username__contains=term) |
                Q(contributor__full_name__contains=term))


class ResourceList(ResourcesView):
    template = 'resources/table_snippets/resource.html'

    def get_queryset(self):
        if self.content_object == 'organization.Project':
            qs = self.get_project().resource_set.all().select_related(
                'contributor')
        else:
            qs = self.get_content_object().resources.all().select_related(
                'contributor')

        if not self.is_superuser or self.get_org_role() is not None:
            return qs.filter(archived=False)

        return qs

    def get(self, *args, **kwargs):
        qs, records_total, records_filtered = self.get_results()

        content_object = self.get_content_object()
        model_type = ContentType.objects.get_for_model(content_object)
        attachments = ContentObject.objects.filter(
            content_type__pk=model_type.id,
            object_id=content_object.id,
            resource_id__in=[resource.id for resource in qs]
        ).values_list('resource_id', 'id')
        attachment_id_dict = dict(attachments)

        for r in qs:
            r.attachment_id = attachment_id_dict.get(r.id)

        return Response({
            'draw': int(self.request.GET.get('draw')),
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': [],
            'tbody': render_to_string(
                self.template,
                context={
                    'resources': qs,
                    'project': self.get_project(),
                    'detatch_redirect': self.request.META['HTTP_REFERER']
                },
                request=self.request)
        })


class ResourceAdd(ResourcesView):
    template = 'resources/table_snippets/resource_add.html'

    def get_queryset(self):
        content_object = self.get_content_object()
        attached = content_object.resources.values_list('id', flat=True)

        qs = self.get_project().resource_set.exclude(
            id__in=attached).select_related('contributor')

        if not self.is_superuser or self.get_org_role() is not None:
            return qs.filter(archived=False)

        return qs

    def get(self, *args, **kwargs):
        qs, records_total, records_filtered = self.get_results()

        return Response({
            'draw': int(self.request.GET.get('draw')),
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': [],
            'tbody': render_to_string(
                self.template,
                context={
                    'resources': qs,
                    'project': self.get_project(),
                    'resource_lib': self.request.path,
                },
                request=self.request)
        })

    def post(self, *args, **kwargs):
        content_object = self.get_content_object()
        qs = self.get_queryset().values_list('id', flat=True)

        resource_to_add = self.request.data['resource']
        if resource_to_add in qs:
            ContentObject.objects.create(
                resource_id=resource_to_add,
                content_object=content_object
            )
            return Response(status=201)
        else:
            return Response(
                data={'detail': _("The resource either is not added to the "
                                  "project or already attached to this "
                                  "object.")},
                status=400)
