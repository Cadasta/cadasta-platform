from django.conf.urls import include, url

from ..views import default


urls = [
    url(
        r'^locations/$',
        default.LocationsList.as_view(),
        name='list'),
    url(
        r'^locations/new/$',
        default.LocationsAdd.as_view(),
        name='add'),
    url(
        r'^locations/(?P<location>[-\w]+)/$',
        default.LocationDetail.as_view(),
        name='detail'),
    url(
        r'^locations/(?P<location>[-\w]+)/edit/$',
        default.LocationEdit.as_view(),
        name='edit'),
    url(
        r'^locations/(?P<location>[-\w]+)/delete/$',
        default.LocationDelete.as_view(),
        name='delete'),

    url(
        r'^locations/(?P<location>[-\w]+)/resources/add/$',
        default.LocationResourceAdd.as_view(),
        name='resource_add'),
    url(
        r'^locations/(?P<location>[-\w]+)/resources/new/$',
        default.LocationResourceNew.as_view(),
        name='resource_new'),

    url(
        r'^locations/(?P<location>[-\w]+)/relationships/new/$',
        default.TenureRelationshipAdd.as_view(),
        name='relationship_add'),
]

urlpatterns = [
    url(
        r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/records/',
        include(urls)),
]
