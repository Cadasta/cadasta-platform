from django.conf.urls import include, url

from ..views import async

urls = [
    url(
        r'^$',
        async.Search.as_view(),
        name='search'),
]

urlpatterns = [
    url(
        r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/search/',
        include(urls)),
]
