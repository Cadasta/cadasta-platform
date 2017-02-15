from django.conf.urls import include, url

from ..views import async


urls = [
    url(
        r'^$',
        async.SpatialUnitList.as_view(),
        name='list'),
    url(
        r'^tiled/(?P<z>[0-9]+)/(?P<x>[0-9]+)/(?P<y>[0-9]+)/$',
        async.SpatialUnitTiles.as_view(),
        name='tiled'),
]


urlpatterns = [
    url(
        r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/spatial/',
        include(urls)),
    # url(urls.tilepath(r'^organizations/(?P<organization>[-\w]+)/projects/'
    #     '(?P<project>[-\w]+)/spatial/'),
    #     async.SpatialUnitList.as_view(),
    #     name='location-tiles'),
]
