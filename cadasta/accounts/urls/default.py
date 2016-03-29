from django.conf.urls import url

from ..views import default

urlpatterns = [
    url(r'^profile/$', default.AccountProfile.as_view(), name='profile'),
]
