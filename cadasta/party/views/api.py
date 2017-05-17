"""Party API."""
from django.db.models import Q
from django.utils.translation import gettext as _
from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from tutelary.mixins import APIPermissionRequiredMixin

from core.mixins import update_permissions
from core.util import paginate_results
from party.models import (PartyRelationship,
                          TenureRelationship)
from spatial.models import SpatialRelationship
from party import serializers
from resources.serializers import ResourceSerializer
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
        'POST': update_permissions('party.create')
    }

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
        'PUT': update_permissions('party.update'),
        'PATCH': update_permissions('party.update'),
        'DELETE': update_permissions('party.delete'),
    }


class PartyResourceList(APIPermissionRequiredMixin,
                        mixins.PartyResourceMixin,
                        generics.ListCreateAPIView):
    serializer_class = ResourceSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('archived',)
    search_fields = ('name', 'description', 'file',)
    ordering_fields = ('name', 'description', 'file',)
    permission_required = {
        'GET': 'party.resources.list',
        'POST': update_permissions('party.resources.add')
    }

    def get_perms_objects(self):
        return [self.get_object()]


class PartyResourceDetail(APIPermissionRequiredMixin,
                          mixins.PartyResourceMixin,
                          generics.RetrieveUpdateDestroyAPIView):
    def patch_actions(self, request):
        if hasattr(request, 'data'):
            if self.get_object().project.archived:
                return False
            is_archived = self.get_object().archived
            new_archived = request.data.get('archived', is_archived)
            if not is_archived and (is_archived != new_archived):
                return ('party.resources.edit', 'party.resources.archive')
        return 'party.resources.edit'

    serializer_class = ResourceSerializer
    permission_required = {
        'GET': 'party.resources.view',
        'PUT': patch_actions,
        'PATCH': patch_actions,
        'DELETE': patch_actions,
    }
    lookup_url_kwarg = 'resource'
    lookup_field = 'id'

    def get_perms_objects(self):
        return [self.get_party()]

    def get_object(self):
        return self.get_resource()

    def destroy(self, request, *args, **kwargs):
        return self.detach_resource(self.kwargs['party'])


class RelationshipList(APIPermissionRequiredMixin,
                       ProjectMixin,
                       APIView):

    permission_required = (
        'spatial_rel.list', 'party_rel.list', 'tenure_rel.list')

    def get(self, request, *args, **kwargs):
        acceptable_classes = ('spatial', 'party', 'tenure')
        rel_class = request.query_params.get('class', None)
        if rel_class is not None and rel_class not in acceptable_classes:
            content = {'detail': _("Relationship class is unknown")}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        spatial_rels = []
        if ('location' in kwargs and
                (rel_class is None or rel_class == 'spatial')):
            manager = SpatialRelationship.objects
            spatial_rels = manager.filter(
                Q(su1=kwargs['location']) | Q(su2=kwargs['location'])
            )

        party_rels = []
        if 'party' in kwargs and (rel_class is None or rel_class == 'party'):
            manager = PartyRelationship.objects
            party_rels = manager.filter(
                Q(party1=kwargs['party']) | Q(party2=kwargs['party'])
            )

        tenure_rels = []
        if rel_class is None or rel_class == 'tenure':
            manager = TenureRelationship.objects
            if 'location' in kwargs:
                tenure_rels = manager.filter(spatial_unit=kwargs['location'])
            elif 'party' in kwargs:
                tenure_rels = (manager.filter(party=kwargs['party']))

        return Response(paginate_results(
            request,
            (spatial_rels, SpatialRelationshipReadSerializer),
            (party_rels, serializers.PartyRelationshipReadSerializer),
            (tenure_rels, serializers.TenureRelationshipReadSerializer),
        ))

    def get_perms_objects(self):
        return [self.get_project()]


class PartyRelationshipCreate(APIPermissionRequiredMixin,
                              mixins.PartyRelationshipQuerySetMixin,
                              generics.CreateAPIView):

    permission_required = update_permissions('party_rel.create')
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
        'PUT': update_permissions('party_rel.update'),
        'PATCH': update_permissions('party_rel.update'),
        'DELETE': update_permissions('party_rel.delete')
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

    permission_required = update_permissions('tenure_rel.create')
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
        'PUT': update_permissions('tenure_rel.update'),
        'PATCH': update_permissions('tenure_rel.update'),
        'DELETE': update_permissions('tenure_rel.delete')
    }

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return serializers.TenureRelationshipWriteSerializer
        else:
            return serializers.TenureRelationshipReadSerializer

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TenureRelationshipResourceList(APIPermissionRequiredMixin,
                                     mixins.TenureRelationshipResourceMixin,
                                     generics.ListCreateAPIView):
    serializer_class = ResourceSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('archived',)
    search_fields = ('name', 'description', 'file',)
    ordering_fields = ('name', 'description', 'file',)
    permission_required = {
        'GET': 'tenure_rel.resources.list',
        'POST': update_permissions('tenure_rel.resources.add')
    }

    def get_perms_objects(self):
        return [self.get_object()]


class TenureRelationshipResourceDetail(APIPermissionRequiredMixin,
                                       mixins.TenureRelationshipResourceMixin,
                                       generics.RetrieveUpdateDestroyAPIView):
    def patch_actions(self, request):
        if hasattr(request, 'data'):
            if self.get_object().project.archived:
                return False
            is_archived = self.get_object().archived
            new_archived = request.data.get('archived', is_archived)
            if not is_archived and (is_archived != new_archived):
                return ('tenure_rel.resources.edit',
                        'tenure_rel.resources.archive')
        return 'tenure_rel.resources.edit'

    serializer_class = ResourceSerializer
    permission_required = {
        'GET': 'tenure_rel.resources.view',
        'PUT': patch_actions,
        'PATCH': patch_actions,
        'DELETE': patch_actions,
    }
    lookup_url_kwarg = 'resource'
    lookup_field = 'id'

    def get_perms_objects(self):
        return [self.get_tenure_relationship()]

    def get_object(self):
        return self.get_resource()

    def destroy(self, request, *args, **kwargs):
        return self.detach_resource(self.kwargs['tenure_rel_id'])
