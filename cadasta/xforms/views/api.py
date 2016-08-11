from django.utils.translation import ugettext as _
from questionnaires.models import Questionnaire
from rest_framework import status, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from tutelary.models import Role
from xforms.mixins.model_helper import ModelHelper
from xforms.mixins.openrosa_headers_mixin import OpenRosaHeadersMixin
from xforms.renderers import XFormListRenderer
from xforms.serializers import XFormListSerializer, XFormSubmissionSerializer

from ..exceptions import XFormOutOfDateError


OPEN_ROSA_ENVELOPE = """
    <OpenRosaResponse xmlns="http://openrosa.org/http/response">
        <message>{message}</message>
    </OpenRosaResponse>
"""


class XFormSubmissionViewSet(OpenRosaHeadersMixin,
                             viewsets.GenericViewSet):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser,)
    serializer_class = XFormSubmissionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if request.method.upper() == 'HEAD':
            return Response(headers=self.get_openrosa_headers(request),
                            status=status.HTTP_204_NO_CONTENT,)
        if serializer.is_valid():
            try:
                data = serializer.save()
            except XFormOutOfDateError as e:
                message = _(OPEN_ROSA_ENVELOPE.format(message=str(e)))
                headers = self.get_openrosa_headers(request, location=False)
                return Response(
                    message, headers=headers, status=status.HTTP_410_GONE)
            ModelHelper().upload_files(request, data)
            return Response(headers=self.get_openrosa_headers(request),
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class XFormListView(OpenRosaHeadersMixin,
                    viewsets.ReadOnlyModelViewSet):

    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (XFormListRenderer,)
    serializer_class = XFormListSerializer

    def get_user_forms(self):
        forms = []
        policies = self.request.user.assigned_policies()
        orgs = self.request.user.organizations.all()
        if Role.objects.get(name='superuser') in policies:
            return Questionnaire.objects.all()
        for org in orgs:
            projects = org.projects.all()
            for project in projects:
                try:
                    questionnaire = Questionnaire.objects.get(
                        id=project.current_questionnaire
                    )
                    forms.append(questionnaire)
                except Questionnaire.DoesNotExist:
                    pass
        return forms

    def get_queryset(self):
        return self.get_user_forms()

    def list(self, request, *args, **kwargs):
        self.object_list = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(self.object_list, many=True)
        return Response(
            serializer.data, headers=self.get_openrosa_headers(request))
