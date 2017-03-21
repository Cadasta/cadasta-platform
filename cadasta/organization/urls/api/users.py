from django.conf.urls import url

from ...views import api

urlpatterns = [
    url(
        r'^$',
        api.UserAdminList.as_view(),
        name='list'),
    url(
        r'^(?P<username>[-\w]+)/$',
        api.UserAdminDetail.as_view(),
        name='detail'),
]
