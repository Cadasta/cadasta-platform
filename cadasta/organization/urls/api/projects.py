from django.conf.urls import url

from ...views import api

urlpatterns = [
    url(
        r'^$',
        api.ProjectList.as_view(),
        name='list'),
]
