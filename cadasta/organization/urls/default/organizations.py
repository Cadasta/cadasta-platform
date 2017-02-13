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
        r'^(?P<organization>[-\w]+)/projects/new/$',
        default.ProjectAddWizard.as_view(),
        name='project-add'),
    # url(
    #     r'^(?P<organization>[-\w]+)/projects/(?P<project>[-\w]+)/#/overview/$',
    #     default.ProjectDashboard.as_view(),
    #     name='project-dashboard'),
    url(
        r'^(?P<organization>[-\w]+)/projects/(?P<project>[-\w]+)/$',
        default.ProjectMap.as_view(),
        name='project-dashboard'),
    url(
        r'^(?P<organization>[-\w]+)/projects/(?P<project>[-\w]+)/edit/'
        'geometry/$',
        default.ProjectEditGeometry.as_view(),
        name='project-edit-geometry'),
    url(
        r'^(?P<organization>[-\w]+)/projects/(?P<project>[-\w]+)/edit/'
        'details/$',
        default.ProjectEditDetails.as_view(),
        name='project-edit-details'),
    url(
        r'^(?P<organization>[-\w]+)/projects/(?P<project>[-\w]+)/edit/'
        'permissions/$',
        default.ProjectEditPermissions.as_view(),
        name='project-edit-permissions'),
    url(
        r'^(?P<organization>[-\w]+)/projects/(?P<project>[-\w]+)/archive/$',
        default.ProjectArchive.as_view(),
        name='project-archive'),
    url(
        r'^(?P<organization>[-\w]+)/projects/(?P<project>[-\w]+)/unarchive/$',
        default.ProjectUnarchive.as_view(),
        name='project-unarchive'),
    url(
        r'^(?P<organization>[-\w]+)/projects/(?P<project>[-\w]+)/download/$',
        default.ProjectDataDownload.as_view(),
        name='project-download'),
    url(
        r'^(?P<organization>[-\w]+)/projects/(?P<project>[-\w]+)/import/$',
        default.ProjectDataImportWizard.as_view(),
        name='project-import'),

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
        r'^(?P<slug>[-\w]+)/members/(?P<username>[-@+.\w]+)/$',
        default.OrganizationMembersEdit.as_view(),
        name='members_edit'),
    url(
        r'^(?P<slug>[-\w]+)/members/(?P<username>[-@+.\w]+)/remove/$',
        default.OrganizationMembersRemove.as_view(),
        name='members_remove'),
]
