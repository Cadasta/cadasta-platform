from django.conf.urls import url

from ..views import default

urlpatterns = [
    url(r'^profile/$', default.AccountProfile.as_view(), name='profile'),
    url(r'^login/$', default.AccountLogin.as_view(), name='login'),
    url(r'^confirm-email/(?P<key>[-:\w]+)/$', default.ConfirmEmail.as_view(),
        name='verify_email'),
    url(r'^password/change/$', default.PasswordChangeView.as_view(),
        name="account_change_password"),
    url(r'^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$',
        default.PasswordResetFromKeyView.as_view(),
        name="account_reset_password_from_key"),
    url(r'^password/reset/$', default.PasswordResetView.as_view(),
        name="account_reset_password"),
    url(r'^account-projects/$', default.AccountListProjects.as_view(),
        name='dashboard'),
]
