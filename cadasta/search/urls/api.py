from django.conf.urls import url

from ..views import api

urlpatterns = [
    url(
        r'^$',
        api.Search.as_view(),
        name='search'),
]
