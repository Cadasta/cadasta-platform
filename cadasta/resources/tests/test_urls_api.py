from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from core.tests.utils.urls import version_ns, version_url

from ..views import api


class RessourceUrlTest(TestCase):
    def test_project_list(self):
        actual = reverse(
            version_ns('resources:project_list'),
            kwargs={'organization': 'habitat',
                    'project': '123abc'}
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/resources/')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/resources/'))
        assert resolved.func.__name__ == api.ProjectResources.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'

    def test_project_detail(self):
        actual = reverse(
            version_ns('resources:project_detail'),
            kwargs={'organization': 'habitat',
                    'project': '123abc',
                    'resource': '456def'}
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/resources/456def/')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/resources/456def/'))
        assert resolved.func.__name__ == api.ProjectResourcesDetail.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
        assert resolved.kwargs['resource'] == '456def'
