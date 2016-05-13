"""Party API."""

from rest_framework import generics, filters
from tutelary.mixins import APIPermissionRequiredMixin

from party import serializers
from . import mixins


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
        'GET': 'project.party.list',
        'POST': 'project.party.create'
    }
    # permission_filter_queryset = ('project.',)


class PartyDetail(APIPermissionRequiredMixin,
                  mixins.PartyQuerySetMixin,
                  generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.PartySerializer
    filter_fields = ('archived',)
    lookup_url_kwarg = 'id'
    lookup_field = 'id'
    permission_required = {
        'GET': 'project.party.view',
        'PATCH': 'project.party.update',
    }
