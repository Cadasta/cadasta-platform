from django.conf.urls import url

from .. import views

urlpatterns = [
    url(
        r'^$',
        views.UserAdminList.as_view(),
        name='list'),
    url(
        r'^(?P<slug>[-\w]+)/$',
        views.UserAdminDetail.as_view(),
        name='detail'),
]
