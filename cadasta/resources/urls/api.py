from django.conf.urls import url

from ..views import api


urlpatterns = [
    url(
        r'^resources/$',
        api.ProjectResources.as_view(),
        name='project_list'),
    url(
        r'^resources/(?P<resource>[-\w]+)/$',
        api.ProjectResourcesDetail.as_view(),
        name='project_detail'),
]
