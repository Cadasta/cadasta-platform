from django.conf.urls import url

from ..views import api

urlpatterns = [
    url(r'^$', api.AccountUser.as_view(), name='user'),
    url(r'^register/$', api.AccountRegister.as_view(), name='register'),
    url(r'^login/$', api.AccountLogin.as_view(), name='login'),
    url(r'^activate/$', api.AccountVerify.as_view(), name='activate'),
    url(r'^password/reset/$', api.PasswordReset.as_view(),
        name='password_reset'),
]
