"""Party API."""

from django.db.models import Q
from django.utils.translation import gettext as _
from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from tutelary.mixins import APIPermissionRequiredMixin

from party.models import (PartyRelationship,
                          TenureRelationship)
from spatial.models import SpatialRelationship
from party import serializers
from spatial.serializers import SpatialRelationshipReadSerializer
from . import mixins
from organization.views.mixins import ProjectMixin


class PartyList(APIPermissionRequiredMixin,
                mixins.PartyQuerySetMixin,
                generics.ListCreateAPIView):

    serializer_class = serializers.PartySerializer
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    filter_fields = ('name', 'type')
    search_fields = ('name',)
    ordering_fields = ('name',)
    permission_required = {
        'GET': 'party.list',
        'POST': 'party.create'
    }
    # permission_filter_queryset = ('project.',)

    def get_perms_objects(self):
        return [self.get_project()]


class PartyDetail(APIPermissionRequiredMixin,
                  mixins.PartyQuerySetMixin,
                  generics.RetrieveUpdateDestroyAPIView):

    serializer_class = serializers.PartySerializer
    filter_fields = ('archived',)
    lookup_url_kwarg = 'party'
    lookup_field = 'id'
    permission_required = {
        'GET': 'party.view',
        'PATCH': 'party.update',
        'DELETE': 'party.delete',
    }


class RelationshipList(APIPermissionRequiredMixin,
                       ProjectMixin,
                       APIView):

    permission_required = (
        'spatial_rel.list', 'party_rel.list', 'tenure_rel.list')

    def get(self, request, *args, **kwargs):

        acceptable_classes = ('spatial', 'party', 'tenure')
        rel_class = self.request.query_params.get('class', None)
        if rel_class is not None and rel_class not in acceptable_classes:
            content = {'detail': _("Relationship class is unknown")}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        spatial_rels = []
        if (
            'spatial_id' in kwargs and
            (rel_class is None or rel_class == 'spatial')
        ):
            manager = SpatialRelationship.objects
            spatial_rels = (
                manager.filter(
                    Q(su1=kwargs['spatial_id']) |
                    Q(su2=kwargs['spatial_id'])
                )
            )
        serialized_spatial_rels = SpatialRelationshipReadSerializer(
            spatial_rels, many=True).data

        party_rels = []
        if (
            'party_id' in kwargs and
            (rel_class is None or rel_class == 'party')
        ):
            manager = PartyRelationship.objects
            party_rels = (
                manager.filter(
                    Q(party1=kwargs['party_id']) |
                    Q(party2=kwargs['party_id'])
                )
            )
        serialized_party_rels = serializers.PartyRelationshipReadSerializer(
            party_rels, many=True).data

        tenure_rels = []
        if rel_class is None or rel_class == 'tenure':
            manager = TenureRelationship.objects
            if 'spatial_id' in kwargs:
                tenure_rels = (
                    manager.filter(spatial_unit=kwargs['spatial_id'])
                )
            elif 'party_id' in kwargs:
                tenure_rels = (
                    manager.filter(party=kwargs['party_id'])
                )
        serialized_tenure_rels = serializers.TenureRelationshipReadSerializer(
            tenure_rels, many=True).data

        return Response(
            serialized_spatial_rels +
            serialized_party_rels +
            serialized_tenure_rels
        )

    def get_perms_objects(self):
        return [self.get_project()]


class PartyRelationshipCreate(APIPermissionRequiredMixin,
                              mixins.PartyRelationshipQuerySetMixin,
                              generics.CreateAPIView):

    permission_required = 'party_rel.create'
    serializer_class = serializers.PartyRelationshipWriteSerializer

    def get_perms_objects(self):
        return [self.get_project()]


class PartyRelationshipDetail(APIPermissionRequiredMixin,
                              mixins.PartyRelationshipQuerySetMixin,
                              generics.RetrieveUpdateDestroyAPIView):

    lookup_url_kwarg = 'party_rel_id'
    lookup_field = 'id'
    permission_required = {
        'GET': 'party_rel.view',
        'PATCH': 'party_rel.update',
        'DELETE': 'party_rel.delete'
    }

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return serializers.PartyRelationshipWriteSerializer
        else:
            return serializers.PartyRelationshipReadSerializer

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TenureRelationshipCreate(APIPermissionRequiredMixin,
                               mixins.TenureRelationshipQuerySetMixin,
                               generics.CreateAPIView):

    permission_required = 'tenure_rel.create'
    serializer_class = serializers.TenureRelationshipWriteSerializer

    def get_perms_objects(self):
        return [self.get_project()]


class TenureRelationshipDetail(APIPermissionRequiredMixin,
                               mixins.TenureRelationshipQuerySetMixin,
                               generics.RetrieveUpdateDestroyAPIView):

    lookup_url_kwarg = 'tenure_rel_id'
    lookup_field = 'id'
    permission_required = {
        'GET': 'tenure_rel.view',
        'PATCH': 'tenure_rel.update',
        'DELETE': 'tenure_rel.delete'
    }

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return serializers.TenureRelationshipWriteSerializer
        else:
            return serializers.TenureRelationshipReadSerializer

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
