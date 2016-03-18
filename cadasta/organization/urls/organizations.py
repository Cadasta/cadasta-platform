from django.conf.urls import url

from .. import views

urlpatterns = [
    url(
        r'^$',
        views.OrganizationList.as_view(),
        name='list'),
    url(
        r'^(?P<slug>[-\w]+)/$',
        views.OrganizationDetail.as_view(),
        name='detail'),
    url(
        r'^(?P<slug>[-\w]+)/users/$',
        views.OrganizationUsers.as_view(),
        name='users'),
    url(
        r'^(?P<slug>[-\w]+)/users/(?P<username>[-\w]+)/$',
        views.OrganizationUsersDetail.as_view(),
        name='users_detail'),
    url(
        r'^(?P<slug>[-\w]+)/projects/$',
        views.ProjectList.as_view(),
        name='project_list'),
    url(
        r'^(?P<slug>[-\w]+)/projects/(?P<project_id>[-\w]+)/users/$',
        views.ProjectUsers.as_view(),
        name='project_users'),
    url(
        r'^(?P<slug>[-\w]+)/projects/(?P<project_id>[-\w]+)/users/(?P<username>[-\w]+)/$',
        views.ProjectUsersDetail.as_view(),
        name='project_users_detail'),
]
