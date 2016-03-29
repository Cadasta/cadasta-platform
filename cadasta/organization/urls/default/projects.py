from django.conf.urls import url

from ...views import default

urlpatterns = [
    url(
        r'^$',
        default.ProjectList.as_view(),
        name='list'),
    url(
        r'^new/$',
        default.ProjectAddWizard.as_view(),
        name='add')
]
