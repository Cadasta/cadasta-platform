from django.conf.urls import url

from ..views import api


urlpatterns = [
    url(
        r'^questionnaire/$',
        api.QuestionnaireDetail.as_view(),
        name='detail'),
]
