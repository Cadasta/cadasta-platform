from django.conf.urls import include, url

from ..views import async


urls = [
    url(
        r'^resources/$',
        async.ResourceList.as_view(),
        name='list'),
    url(
        r'^parties/(?P<object_id>[-\w]+)/resources/$',
        async.ResourceList.as_view(content_object='party.Party'),
        name='party'),
    url(
        r'^locations/(?P<object_id>[-\w]+)/resources/$',
        async.ResourceList.as_view(
            content_object='spatial.SpatialUnit',
            template='resources/table_snippets/resource_sm.html'),
        name='location'),
    url(
        r'^relationships/(?P<object_id>[-\w]+)/resources/$',
        async.ResourceList.as_view(
            content_object='party.TenureRelationship',
            template='resources/table_snippets/resource_sm.html'),
        name='relationship'),
    url(
        r'^resources/add/$',
        async.ResourceAdd.as_view(),
        name='add_to_project'),
    url(
        r'^parties/(?P<object_id>[-\w]+)/resources/add/$',
        async.ResourceAdd.as_view(content_object='party.Party'),
        name='add_to_party'),
    url(
        r'^locations/(?P<object_id>[-\w]+)/resources/add/$',
        async.ResourceAdd.as_view(content_object='spatial.SpatialUnit'),
        name='add_to_location'),
    url(
        r'^relationships/(?P<object_id>[-\w]+)/resources/add/$',
        async.ResourceAdd.as_view(content_object='party.TenureRelationship'),
        name='add_to_relationship'),
]


urlpatterns = [
    url(
        r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/',
        include(urls)),
]
