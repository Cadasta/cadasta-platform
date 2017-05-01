from django.conf.urls import url, include

from . import views

urls = [
    url(
        r'^_search/$',
        views.Search.as_view(),
        name='search'),
    url(
        r'^_data/$',
        views.Dump.as_view(),
        name='dump'),
]

urlpatterns = [
    url(
        r'^project-(?P<projectid>[-\w]+)/(?P<type>[-\w,]+)/',
        include(urls, namespace='mock_es')),
]
