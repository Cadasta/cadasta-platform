from django.conf.urls import url

from ...views import api

urlpatterns = [
    url(
        r'^$',
        api.OrganizationList.as_view(),
        name='list'),
    url(
        r'^(?P<organization>[-\w]+)/$',
        api.OrganizationDetail.as_view(),
        name='detail'),
    url(
        r'^(?P<organization>[-\w]+)/users/$',
        api.OrganizationUsers.as_view(),
        name='users'),
    url(
        r'^(?P<organization>[-\w]+)/users/(?P<username>[-@+.\w]+)/$',
        api.OrganizationUsersDetail.as_view(),
        name='users_detail'),
    url(
        r'^(?P<organization>[-\w]+)/projects/$',
        api.OrganizationProjectList.as_view(),
        name='project_list'),
    url(
        r'^(?P<organization>[-\w]+)/projects/(?P<project>[-\w]+)/$',
        api.ProjectDetail.as_view(),
        name='project_detail'),
    url(
        r'^(?P<organization>[-\w]+)/projects/(?P<project>[-\w]+)/users/$',
        api.ProjectUsers.as_view(),
        name='project_users'),
    url(
        r'^(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/users/(?P<username>[-@+.\w]+)/$',
        api.ProjectUsersDetail.as_view(),
        name='project_users_detail'),
]
