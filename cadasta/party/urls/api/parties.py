from django.conf.urls import url

from party.views import api

urlpatterns = [
    url(
        r'^$',
        api.PartyList.as_view(),
        name='list'),
    url(
        r'^(?P<party>[-\w]+)/$',
        api.PartyDetail.as_view(),
        name='detail'),
    url(
        r'^(?P<party>[-\w]+)/resources/(?P<resource>[-\w]+)/$',
        api.PartyResourceDetail.as_view(),
        name='resource_detail'),
    url(
        r'^(?P<party>[-\w]+)/resources/$',
        api.PartyResourceList.as_view(),
        name='resource_list'),
    url(
        r'^(?P<party>[-\w]+)/relationships/$',
        api.RelationshipList.as_view(),
        name='rel_list'),
]
