from django.conf.urls import url

from spatial.views import api as spatial_api
from party.views import api as party_api

urlpatterns = [
    url(
        r'^spatial/$',
        spatial_api.SpatialRelationshipCreate.as_view(),
        name='spatial_rel_create'),
    url(
        r'^spatial/(?P<spatial_rel_id>[-\w]+)/$',
        spatial_api.SpatialRelationshipDetail.as_view(),
        name='spatial_rel_detail'),
    url(
        r'^party/$',
        party_api.PartyRelationshipCreate.as_view(),
        name='party_rel_create'),
    url(
        r'^party/(?P<party_rel_id>[-\w]+)/$',
        party_api.PartyRelationshipDetail.as_view(),
        name='party_rel_detail'),
    url(
        r'^tenure/(?P<tenure_rel_id>[-\w]+)/$',
        party_api.TenureRelationshipDetail.as_view(),
        name='tenure_rel_detail'),
    url(
        r'^tenure/$',
        party_api.TenureRelationshipCreate.as_view(),
        name='tenure_rel_create'),
    url(
        (r'^tenure/(?P<tenure_rel_id>[-\w]+)/resources/'
         '(?P<resource>[-\w]+)/$'),
        party_api.TenureRelationshipResourceDetail.as_view(),
        name='tenure_rel_resource_detail'),
    url(
        r'^tenure/(?P<tenure_rel_id>[-\w]+)/resources/$',
        party_api.TenureRelationshipResourceList.as_view(),
        name='tenure_rel_resource_list'),
]
