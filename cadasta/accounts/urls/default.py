from django.conf.urls import url

from ..views import default

urlpatterns = [
    url(r'^profile/$', default.AccountProfile.as_view(), name='profile'),
    url(r'^login/$', default.AccountLogin.as_view(), name='login'),
    url(r'^confirm-email/(?P<key>[-:\w]+)/$', default.ConfirmEmail.as_view(),
        name='verify_email'),
]
