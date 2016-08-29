from django.conf.urls import include, url

from ..views import default


urls = [
    url(
        r'^resources/$',
        default.ProjectResources.as_view(),
        name='project_list'),
    url(
        r'^resources/add/$',
        default.ProjectResourcesAdd.as_view(),
        name='project_add_existing'),
    url(
        r'^resources/add/new/$',
        default.ProjectResourcesNew.as_view(),
        name='project_add_new'),
    url(
        r'^resources/(?P<resource>[-\w]+)/$',
        default.ProjectResourcesDetail.as_view(),
        name='project_detail'),
    url(
        r'^resources/(?P<resource>[-\w]+)/edit/$',
        default.ProjectResourcesEdit.as_view(),
        name='project_edit'),
    url(
        r'^resources/(?P<resource>[-\w]+)/archive/$',
        default.ResourceArchive.as_view(),
        name='archive'),
    url(
        r'^resources/(?P<resource>[-\w]+)/unarchive/$',
        default.ResourceUnarchive.as_view(),
        name='unarchive'),
    url(
        r'^resources/(?P<resource>[-\w]+)/detach/(?P<attachment>[-\w]+)/$',
        default.ResourceDetach.as_view(),
        name='detach'),
]

urlpatterns = [
    url(
        r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/',
        include(urls)),
]
