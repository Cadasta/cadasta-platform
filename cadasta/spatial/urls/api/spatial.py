from django.conf.urls import url

from ...views import api

urlpatterns = [
    url(
        r'^$',
        api.SpatialUnitList.as_view(),
        name='list'),
    url(
        r'^(?P<spatial_id>[-\w]+)/',
        api.SpatialUnitDetail.as_view(),
        name='view'),
]
