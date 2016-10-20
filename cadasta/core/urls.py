from django.conf.urls import url

from core.views import default

urlpatterns = [
    url(r'^$', default.IndexPage.as_view(), name='index'),
    url(r'^dashboard/$', default.Dashboard.as_view(), name='dashboard'),
]
