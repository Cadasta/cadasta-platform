import logging

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.six import BytesIO
from django.utils.translation import ugettext as _
from questionnaires.models import Questionnaire
from rest_framework import status, viewsets, generics
from rest_framework.authentication import BasicAuthentication
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from tutelary.models import Role
from tutelary.mixins import APIPermissionRequiredMixin
from xforms.models import XFormSubmission
from xforms.mixins.model_helper import ModelHelper
from xforms.mixins.openrosa_headers_mixin import OpenRosaHeadersMixin
from xforms.renderers import XFormListRenderer
from xforms.serializers import XFormListSerializer, XFormSubmissionSerializer
from xforms.exceptions import InvalidXMLSubmission
from questionnaires.serializers import QuestionnaireSerializer
from ..renderers import XFormRenderer

logger = logging.getLogger('xform.submissions')

OPEN_ROSA_ENVELOPE = """
    <OpenRosaResponse xmlns="http://openrosa.org/http/response">
        <message>{message}</message>
    </OpenRosaResponse>
"""


class XFormSubmissionViewSet(OpenRosaHeadersMixin, viewsets.GenericViewSet):
    """
    Serves up the /collect/submissions/ api requests.

    Serializes and creates party, spatial, and tenure relationship models
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
        try:
            instance = ModelHelper().upload_submission_data(request)
        except InvalidXMLSubmission as e:
            logger.debug(str(e))
            return self._sendErrorResponse(request, e,
                                           status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return self._sendErrorResponse(request, e,
                                           status.HTTP_403_FORBIDDEN)

        # If an already existing XFormSummission is sent back
        # don't create another.
        if type(instance) == XFormSubmission:
            return Response(
                headers=self.get_openrosa_headers(request),
                status=status.HTTP_201_CREATED,
                content_type='application/xml'
            )

        instance, parties, locations, tenure_relationships = instance
        serializer = XFormSubmissionSerializer(instance)

        json = JSONRenderer().render(serializer.data)
        stream = BytesIO(json)
        data = JSONParser().parse(stream)
        serializer = XFormSubmissionSerializer(data=data)

        # Every possible error that would make the serializer not valid
        # has already been checked for, so no failsafe is necessary.
        if serializer.is_valid():
            data = serializer.save()
            data.parties.add(*parties)
            data.spatial_units.add(*locations)
            data.tenure_relationships.add(*tenure_relationships)

            return Response(
                headers=self.get_openrosa_headers(request),
                status=status.HTTP_201_CREATED,
                content_type='application/xml'
            )

    def _sendErrorResponse(self, request, e, status):
        message = _(OPEN_ROSA_ENVELOPE.format(message=str(e)))
        headers = self.get_openrosa_headers(
            request, location=False, content_length=False)
        return Response(
            message, status=status,
            headers=headers, content_type='application/xml'
        )


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

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context['request'] = self.request
        return context

    def get_user_forms(self):
        forms = []
        policies = self.request.user.assigned_policies()
        orgs = self.request.user.organizations.filter(archived=False)
        if Role.objects.get(name='superuser') in policies:
            return Questionnaire.objects.filter(project__archived=False)
        for org in orgs:
            projects = org.projects.filter(archived=False)
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


class XFormDownloadView(APIPermissionRequiredMixin, generics.RetrieveAPIView):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (XFormRenderer,)
    serializer_class = QuestionnaireSerializer
    permission_required = 'questionnaire.view'

    def get_perms_objects(self):
        return [self.get_object().project]

    def get_object(self):
        if not hasattr(self, '_object'):
            self._object = get_object_or_404(
                Questionnaire, id=self.kwargs['questionnaire'])

        return self._object

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context['project'] = self.get_object().project
        return context
