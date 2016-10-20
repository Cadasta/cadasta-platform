from django.conf.urls import url

from spatial.views import api
from party.views.api import RelationshipList

urlpatterns = [
    url(
        r'^$',
        api.SpatialUnitList.as_view(),
        name='list'),
    url(
        r'^(?P<location>[-\w]+)/$',
        api.SpatialUnitDetail.as_view(),
        name='detail'),
    url(
        r'^(?P<location>[-\w]+)/relationships/$',
        RelationshipList.as_view(),
        name='rel_list'),
    url(
        r'^(?P<location>[-\w]+)/resources/(?P<resource>[-\w]+)/$',
        api.SpatialUnitResourceDetail.as_view(),
        name='resource_detail'),
    url(
        r'^(?P<location>[-\w]+)/resources/',
        api.SpatialUnitResourceList.as_view(),
        name='resource_list'),
]
