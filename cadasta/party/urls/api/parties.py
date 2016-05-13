from django.conf.urls import url

from ...views import api

urlpatterns = [
    url(
        r'^$',
        api.PartyList.as_view(),
        name='list'),
    url(
        r'^(?P<id>[-\w]+)/$',
        api.PartyDetail.as_view(),
        name='detail'),
]
