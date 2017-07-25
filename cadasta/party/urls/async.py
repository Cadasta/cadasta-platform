from django.conf.urls import include, url

from ..views import async


urls = [
    url(
        r'^$',
        async.PartyList.as_view(),
        name='list'),
]


urlpatterns = [
    url(
        r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/parties/',
        include(urls)),
]
