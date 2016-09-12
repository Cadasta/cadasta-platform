from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework import generics, mixins, status
from rest_framework.response import Response
from tutelary.mixins import APIPermissionRequiredMixin

from organization.models import Project
from ..models import Questionnaire
from ..serializers import QuestionnaireSerializer
from ..exceptions import InvalidXLSForm


class QuestionnaireDetail(APIPermissionRequiredMixin,
                          mixins.CreateModelMixin,
                          generics.RetrieveUpdateAPIView):
    def patch_actions(self, request):
        try:
            self.get_object()
            # return ('questionnaire.edit')
        except Questionnaire.DoesNotExist:
            return ('questionnaire.add')

    serializer_class = QuestionnaireSerializer
    permission_required = {
        'GET': 'questionnaire.view',
        'PUT': patch_actions,
    }

    def get_perms_objects(self):
        return [self.get_project()]

    def get_project(self):
        if not hasattr(self, 'project_object'):
            org_slug = self.kwargs['organization']
            prj_slug = self.kwargs['project']

            self.project_object = get_object_or_404(
                Project,
                organization__slug=org_slug,
                slug=prj_slug
            )

        return self.project_object

    def handle_exception(self, exc):
        if isinstance(exc, InvalidXLSForm):
            return Response({'xls_form': exc.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            return super().handle_exception(exc)

    def get_object(self):
        if not hasattr(self, 'object'):
            prj = self.get_project()
            self.object = Questionnaire.objects.get(
                id=prj.current_questionnaire)

        return self.object

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context['project'] = self.get_project()
        return context

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Questionnaire.DoesNotExist:
            raise Http404('No Questionnaire matches the given query.')

    def put(self, request, *args, **kwargs):
        return self.create(request)
