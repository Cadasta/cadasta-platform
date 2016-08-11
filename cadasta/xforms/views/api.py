from django.utils.six import BytesIO
from rest_framework import status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.authentication import (BasicAuthentication,)
from rest_framework.permissions import IsAuthenticated

from tutelary.models import Role
from questionnaires.models import Questionnaire
from xforms.mixins.model_helper import ModelHelper
from xforms.serializers import XFormListSerializer, XFormSubmissionSerializer
from xforms.renderers import XFormListRenderer
from xforms.mixins.openrosa_headers_mixin import OpenRosaHeadersMixin


class XFormSubmissionViewSet(OpenRosaHeadersMixin,
                             viewsets.GenericViewSet):
    """
    Serves up the /collect/submissions/ api requests
    Serializes and creates party, spatial, and tunure relationships models
    Stores images in S3 buckets
    Returns number of successful forms submitted
    """

    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser,)
    serializer_class = XFormSubmissionSerializer

    def create(self, request, *args, **kwargs):
        if request.method.upper() == 'HEAD':
            return Response(headers=self.get_openrosa_headers(request),
                            status=status.HTTP_204_NO_CONTENT,)

        instance = ModelHelper(
            ).upload_submission_data(request)

        if type(instance) == Response:
            return instance

        serializer = XFormSubmissionSerializer(instance)

        json = JSONRenderer().render(serializer.data)
        stream = BytesIO(json)
        data = JSONParser().parse(stream)

        serializer = XFormSubmissionSerializer(data=data)
        # Every possible error that would make the serializer not valid
        # has already been checked for, so no failsafe is necessary.
        if serializer.is_valid():
            data = serializer.save()
            return Response(headers=self.get_openrosa_headers(request),
                            status=status.HTTP_201_CREATED)


class XFormListView(OpenRosaHeadersMixin,
                    viewsets.ReadOnlyModelViewSet):
    """
    Returns the current_questionnaires from all of the
    projects a user is a member of.
    """

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
