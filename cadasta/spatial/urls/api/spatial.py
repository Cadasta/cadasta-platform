from django.conf.urls import url

from spatial.views import api
from party.views.api import RelationshipList

urlpatterns = [
    url(
        r'^$',
        api.SpatialUnitList.as_view(),
        name='list'),
    url(
        r'^(?P<spatial_id>[-\w]+)/$',
        api.SpatialUnitDetail.as_view(),
        name='detail'),
    url(
        r'^(?P<spatial_id>[-\w]+)/relationships/$',
        RelationshipList.as_view(),
        name='rel_list'),
]
