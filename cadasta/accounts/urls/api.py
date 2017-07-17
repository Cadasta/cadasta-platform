from django.conf.urls import url

from ..views import api

urlpatterns = [
    url(r'^$', api.AccountUser.as_view(), name='user'),
    url(r'^register/$', api.AccountRegister.as_view(), name='register'),
    url(r'^login/$', api.AccountLogin.as_view(), name='login'),
    url(r'^password/$', api.SetPasswordView.as_view(), name='password'),
    url(r'^verify/phone/$', api.ConfirmPhoneView.as_view(),
        name='verify_phone')
]
