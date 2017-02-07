from django.conf.urls import url

from ..views import default

urlpatterns = [
    url(
        r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/search/',
        default.Search.as_view(),
        name='search'),
]
