from rest_framework.response import Response
from rest_framework import generics
from rest_framework import filters, status

from tutelary.mixins import APIPermissionRequiredMixin

from spatial.serializers import SpatialUnitSerializer
from .mixins import SpatialQuerySetMixin


class SpatialUnitList(APIPermissionRequiredMixin,
                      SpatialQuerySetMixin,
                      generics.ListCreateAPIView):
    serializer_class = SpatialUnitSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)
    filter_fields = ('type',)
    search_fields = ('name',)
    ordering_fields = ('name',)

    permission_required = {
        'GET': 'spatial.list',
        'POST': 'spatial.add',
    }

    def get_queryset(self):
        return super().get_queryset().filter(
            project__slug=self.kwargs['project_slug'])


class SpatialUnitDetail(APIPermissionRequiredMixin,
                        SpatialQuerySetMixin,
                        generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SpatialUnitSerializer
    lookup_url_kwarg = 'spatial_id'
    lookup_field = 'id'
    permission_required = {
        'GET': 'spatial.view',
        'PATCH': 'spatial.update',
        'DELETE': 'spatial.delete'
    }

    def get_queryset(self):
        return super().get_queryset().filter(id=self.kwargs['spatial_id'])

    def destroy(self, request, *args, **kwargs):
        su = self.get_object()
        role = self.proj.spatial_units.get(id=su.id)
        role.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
