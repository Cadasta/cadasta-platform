from django.conf.urls import url

from ...views import default

urlpatterns = [
    url(
        r'^$',
        default.OrganizationList.as_view(),
        name='list'),
    url(
        r'^new/$',
        default.OrganizationAdd.as_view(),
        name='add'),
    url(
        r'^(?P<slug>[-\w]+)/$',
        default.OrganizationDashboard.as_view(),
        name='dashboard'),
    url(
        r'^(?P<slug>[-\w]+)/edit/$',
        default.OrganizationEdit.as_view(),
        name='edit'),
    url(
        r'^(?P<slug>[-\w]+)/archive/$',
        default.OrganizationArchive.as_view(),
        name='archive'),
    url(
        r'^(?P<slug>[-\w]+)/unarchive/$',
        default.OrganizationUnarchive.as_view(),
        name='unarchive'),
    #
    # PROJECTS
    #

    url(
        r'^(?P<organization>[-\w]+)/projects/(?P<project>[-\w]+)/$',
        default.ProjectDashboard.as_view(),
        name='project-dashboard'),
    url(
        r'^(?P<organization>[-\w]+)/projects/(?P<project>[-\w]+)/edit/$',
        default.ProjectEdit.as_view(),
        name='project-edit'),

    #
    # MEMBERS
    #

    url(
        r'^(?P<slug>[-\w]+)/members/$',
        default.OrganizationMembers.as_view(),
        name='members'),
    url(
        r'^(?P<slug>[-\w]+)/members/add/$',
        default.OrganizationMembersAdd.as_view(),
        name='members_add'),
    url(
        r'^(?P<slug>[-\w]+)/members/(?P<username>[-\w]+)/$',
        default.OrganizationMembersEdit.as_view(),
        name='members_edit'),
    url(
        r'^(?P<slug>[-\w]+)/members/(?P<username>[-\w]+)/remove/$',
        default.OrganizationMembersRemove.as_view(),
        name='members_remove'),
]
