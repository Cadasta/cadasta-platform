from django.db.models import OuterRef, Subquery
from tutelary.mixins import APIPermissionRequiredMixin
from rest_framework import generics
from rest_framework_gis.pagination import GeoJsonPagination

from questionnaires.models import QuestionOption

from . import mixins
from .. import serializers


from django.core.paginator import Paginator


class SpatialUnitDjangoPaginator(Paginator):

    def page(self, number):
        page = super().page(number)
        # Here we are adding annotation after the page is selected. This helps
        # us avoid the burden of the annotation's lookup clauses when we are
        # doing the COUNT() operation needed to create the page.
        annotation = {
            # Prefetch the location type name
            page.object_list.model._LOCATION_TYPE_KEY: Subquery(
                QuestionOption.objects.filter(
                    question__questionnaire_id=OuterRef(
                        'project__current_questionnaire'),
                    name=OuterRef('type')
                ).values('label_xlat')
            )
        }
        page.object_list = page.object_list.annotate(**annotation)
        return page


class SpatialUnitPaginator(GeoJsonPagination):
    page_size = 1000
    django_paginator_class = SpatialUnitDjangoPaginator


class SpatialUnitList(APIPermissionRequiredMixin,
                      mixins.SpatialQuerySetMixin,
                      generics.ListAPIView):
    pagination_class = SpatialUnitPaginator
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
        return queryset

    def get_perms_objects(self):
        return [self.get_project()]
