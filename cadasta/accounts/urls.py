from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns(
    '',
    url(r'^$', views.AccountUser.as_view(), name='user'),
    url(r'^register/$', views.AccountRegister.as_view(), name='register'),
    url(r'^login/$', views.AccountLogin.as_view(), name='login'),
    url(r'^activate/$', views.AccountVerify.as_view(), name='activate'),
    url(r'^password/reset/$', views.PasswordReset.as_view(), name='password_reset'),
)
