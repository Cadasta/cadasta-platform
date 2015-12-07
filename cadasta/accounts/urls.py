from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns(
    '',
    url(r'^register/$', views.AccountRegister.as_view(), name='register'),
    url(r'^login/$', views.AccountLogin.as_view(), name='login'),
)
