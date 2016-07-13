from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser

# from xforms.util.authentication import DigestAuthentication
# from rest_framework_digestauth.authentication import DigestAuthentication
from rest_framework.authentication import (BasicAuthentication,)
from rest_framework.permissions import IsAuthenticated
from questionnaires.models import Questionnaire
from xforms.mixins.model_helper import ModelHelper

from tutelary.models import Role

from xforms.serializers import XFormListSerializer, XFormSubmissionSerializer
from xforms.renderers import XFormListRenderer
from rest_framework import viewsets
from rest_framework.response import Response

from xforms.mixins.openrosa_headers_mixin import OpenRosaHeadersMixin


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
            data = serializer.save()
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
            forms.extend(Questionnaire.objects.filter(
                project__organization=org))
        return forms

    def get_queryset(self):
        return self.get_user_forms()

    def list(self, request, *args, **kwargs):
        self.object_list = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(self.object_list, many=True)
        return Response(
            serializer.data, headers=self.get_openrosa_headers(request))
