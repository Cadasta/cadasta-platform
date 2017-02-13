from django.conf.urls import include, url

from ..views import async


urls = [
    url(
        r'^records/relationship/(?P<relationship>[-\w]+)/$',
        async.PartyRelationshipDetail.as_view(),
        name='relationship_detail'),
    url(
        r'^records/relationship/(?P<relationship>[-\w]+)/edit/$',
        async.PartyRelationshipEdit.as_view(),
        name='relationship_edit'),
    url(
        r'^records/relationship/(?P<relationship>[-\w]+)/delete/$',
        async.PartyRelationshipDelete.as_view(),
        name='relationship_delete'),
    url(
        r'^records/relationship/(?P<relationship>[-\w]+)/resources/add/$',
        async.PartyRelationshipResourceAdd.as_view(),
        name='relationship_resource_add'),
    url(
        r'^records/relationship/(?P<relationship>[-\w]+)/resources/new/$',
        async.PartyRelationshipResourceNew.as_view(),
        name='relationship_resource_new'),
]


urlpatterns = [
    url(
        r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/',
        include(urls)),
]
