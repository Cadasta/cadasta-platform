"""cadasta URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url, handler500
from django.views.i18n import javascript_catalog


server_error_handler = handler500

server_error_handler = 'core.views.default.server_error'

api_v1 = [
    url(r'^account/', include('accounts.urls.api', namespace='accounts')),
    url(r'^account/', include('djoser.urls.authtoken')),

    url(r'^organizations/',
        include('organization.urls.api.organizations',
                namespace='organization')),
    url(r'^projects/',
        include('organization.urls.api.projects',
                namespace='project')),
    url(r'^users/',
        include('organization.urls.api.users',
                namespace='user')),
    url(r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/',
        include('questionnaires.urls.api',
                namespace='questionnaires')),
    url(r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/',
        include('resources.urls.api',
                namespace='resources')),
    url(r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/spatial/',
        include('spatial.urls.api.spatial',
                namespace='spatial')),
    url(r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/parties/',
        include('party.urls.api.parties',
                namespace='party')),
    url(r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/relationships/',
        include('party.urls.api.relationships',
                namespace='relationship')),
    url(r'^organizations/(?P<organization>[-\w]+)/projects/'
        '(?P<project>[-\w]+)/search/',
        include('search.urls.api',
                namespace='search')),

    url(r'^docs/',
        include('rest_framework_docs.urls'))
]

api = [
    url(r'^v1/', include(api_v1, namespace='v1'))
]

async = [
    url(r'^',
        include('spatial.urls.async',
                namespace='spatial')),
]

urlpatterns = [
    url(r'^',
        include('core.urls',
                namespace='core')),
    url(r'^account/',
        include('accounts.urls.default',
                namespace='account')),
    url(r'^account/',
        include('allauth.urls')),
    url('^',
        include('django.contrib.auth.urls')),
    url(r'^organizations/',
        include('organization.urls.default.organizations',
                namespace='organization')),
    url(r'^projects/',
        include('organization.urls.default.projects',
                namespace='project')),
    url(r'^users/',
        include('organization.urls.default.users',
                namespace='user')),
    url(r'^',
        include('party.urls.default',
                namespace='parties')),
    url(r'^',
        include('spatial.urls.default',
                namespace='locations')),
    url(r'^',
        include('resources.urls.default',
                namespace='resources')),
    url(r'^',
        include('search.urls.default',
                namespace='search')),

    url(r'^api/',
        include(api,
                namespace='api')),
    url(r'^async/',
        include(async,
                namespace='async')),
    url(r'^collect/', include('xforms.urls.api')),

    url(r'^i18n/',
        include('django.conf.urls.i18n')),
    url(r'^jsi18n/', javascript_catalog, {}, name='javascript-catalog'),
]
