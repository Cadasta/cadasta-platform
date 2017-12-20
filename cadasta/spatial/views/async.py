from django.db.models import OuterRef, Subquery
from tutelary.mixins import APIPermissionRequiredMixin
from rest_framework import generics
from rest_framework_gis.pagination import GeoJsonPagination

from questionnaires.models import QuestionOption

from . import mixins
from .. import serializers


class Paginator(GeoJsonPagination):
    page_size = 1000


class SpatialUnitList(APIPermissionRequiredMixin,
                      mixins.SpatialQuerySetMixin,
                      generics.ListAPIView):
    pagination_class = Paginator
    serializer_class = serializers.SpatialUnitGeoJsonSerializer

    def get_actions(self, request):
        if self.get_project().archived:
            return ['project.view_archived', 'spatial.list']
        if self.get_project().public():
            return ['project.view', 'spatial.list']
        else:
            return ['project.view_private', 'spatial.list']

    permission_required = {
        'GET': get_actions
    }

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        queryset = queryset.exclude(id=self.request.GET.get('exclude'))
        annotation = {
            # Prefetch the location type name
            queryset.model._LOCATION_TYPE_KEY: Subquery(
                QuestionOption.objects.filter(
                    question__questionnaire_id=OuterRef(
                        'project__current_questionnaire'),
                    name=OuterRef('type')
                ).values('label_xlat')
            )
        }
        return queryset.annotate(**annotation)

    def get_perms_objects(self):
        return [self.get_project()]
