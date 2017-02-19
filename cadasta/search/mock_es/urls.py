from django.conf.urls import url, include

from . import views

urls = [
    url(
        r'^_search/',
        views.EsAllTypes.as_view(),
        name='all'),
    url(
        r'^(?P<type>[-\w]+)/_search/',
        views.EsSingleType.as_view(),
        name='type'),
]

urlpatterns = [
    url(
        r'^project-(?P<projectid>[-\w]+)/',
        include(urls, namespace='mock_es')),
]
