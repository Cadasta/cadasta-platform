from django.conf.urls import include, url

from ..views import default


urls = [
    url(
        r'^parties/$',
        default.PartiesList.as_view(),
        name='list'),
    url(
        r'^parties/new/$',
        default.PartiesAdd.as_view(),
        name='add'),
    url(
        r'^parties/(?P<party>[-\w]+)/$',
        default.PartiesDetail.as_view(),
        name='detail'),
    url(
        r'^parties/(?P<party>[-\w]+)/edit/$',
        default.PartiesEdit.as_view(),
        name='edit'),
    url(
        r'^parties/(?P<party>[-\w]+)/delete/$',
        default.PartiesDelete.as_view(),
        name='delete'),

    url(
        r'^parties/(?P<party>[-\w]+)/resources/add/$',
        default.PartyResourcesAdd.as_view(),
        name='resource_add'),
    url(
        r'^parties/(?P<party>[-\w]+)/resources/new/$',
        default.PartyResourcesNew.as_view(),
        name='resource_new'),
]

relationship_urls = [
    # url(
    #     r'^relationships/(?P<relationship>[-\w]+)/$',
    #     default.PartyRelationshipDetail.as_view(),
    #     name='relationship_detail'),
    # url(
    #     r'^relationships/(?P<relationship>[-\w]+)/edit/$',
    #     default.PartyRelationshipEdit.as_view(),
    #     name='relationship_edit'),
    # url(
    #     r'^relationships/(?P<relationship>[-\w]+)/delete/$',
    #     default.PartyRelationshipDelete.as_view(),
    #     name='relationship_delete'),
    # url(
    #     r'^relationships/(?P<relationship>[-\w]+)/resources/add/$',
    #     default.PartyRelationshipResourceAdd.as_view(),
    #     name='relationship_resource_add'),
    # url(
    #     r'^relationships/(?P<relationship>[-\w]+)/resources/new/$',
    #     default.PartyRelationshipResourceNew.as_view(),
    #     name='relationship_resource_new'),
]

urlpatterns = [
    url(
        r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/',
        include(relationship_urls)),
    url(
        r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/records/',
        include(urls)),
]
