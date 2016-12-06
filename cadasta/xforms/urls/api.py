from django.conf.urls import url
from ..views import api

urlpatterns = [
    url(r'^$', api.XFormListView.as_view(
        {'get': 'list'}), name='form-list'),
    url(r'^formList/$', api.XFormListView.as_view(
        {'get': 'list'}), name='form-list'),
    url(r'^formList/(?P<questionnaire>[-\w]+)/$',
        api.XFormDownloadView.as_view(), name='form-download'),
    url(r'^submission$',
        api.XFormSubmissionViewSet.as_view(
            {'post': 'create', 'head': 'create'}),
        name='submissions'),
]
