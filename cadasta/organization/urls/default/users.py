from django.conf.urls import url

from ...views import default

urlpatterns = [
    url(r'^$', default.UserList.as_view(), name='list'),
    url(r'^(?P<user>[-\w]+)/activate/$',
        default.UserActivation.as_view(new_state=True),
        name='activate'),
    url(r'^(?P<user>[-\w]+)/deactivate/$',
        default.UserActivation.as_view(new_state=False),
        name='deactivate')
]
