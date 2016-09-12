from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from core.tests.utils.urls import version_ns, version_url

from ..views import api
from spatial.views import api as api2


class PartyUrlTest(TestCase):

    def test_project_party_list(self):
        actual = reverse(
            version_ns('party:list'),
            kwargs={
                'organization': 'habitat',
                'project': '123abc',
            }
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/parties/')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/parties/'))
        assert resolved.func.__name__ == api.PartyList.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'

    def test_project_party_detail(self):
        actual = reverse(
            version_ns('party:detail'),
            kwargs={
                'organization': 'habitat',
                'project': '123abc',
                'party': '123456123456123456123456',
            }
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/'
            'parties/123456123456123456123456/')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/'
            'parties/123456123456123456123456/'))
        assert resolved.func.__name__ == api.PartyDetail.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
        assert resolved.kwargs['party'] == '123456123456123456123456'

    def test_project_party_relationships_list(self):
        actual = reverse(
            version_ns('party:rel_list'),
            kwargs={
                'organization': 'habitat',
                'project': '123abc',
                'party': '123456123456123456123456',
            }
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/'
            'parties/123456123456123456123456/relationships/')
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/'
            'parties/123456123456123456123456/relationships/'))
        assert resolved.func.__name__ == api.RelationshipList.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
        assert resolved.kwargs['party'] == '123456123456123456123456'


class RelationshipUrlTest(TestCase):

    def generic_test_project_relationship_create(self, rel_class, view):
        actual = reverse(
            version_ns('relationship:{}_rel_create'.format(rel_class)),
            kwargs={
                'organization': 'habitat',
                'project': '123abc',
            }
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/'
            'relationships/{}/'.format(rel_class))
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/'
            'relationships/{}/'.format(rel_class)))
        assert resolved.func.__name__ == view.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'

    def generic_test_project_relationship_detail(self, rel_class, view):
        actual = reverse(
            version_ns('relationship:{}_rel_detail'.format(rel_class)),
            kwargs={
                'organization': 'habitat',
                'project': '123abc',
                '{}_rel_id'.format(rel_class): '654321654321654321654321',
            }
        )
        expected = version_url(
            '/organizations/habitat/projects/123abc/'
            'relationships/{}/654321654321654321654321/'.format(rel_class))
        assert actual == expected

        resolved = resolve(version_url(
            '/organizations/habitat/projects/123abc/'
            'relationships/{}/654321654321654321654321/'.format(rel_class)))
        assert resolved.func.__name__ == view.__name__
        assert resolved.kwargs['organization'] == 'habitat'
        assert resolved.kwargs['project'] == '123abc'
        assert resolved.kwargs['{}_rel_id'.format(rel_class)] == (
            '654321654321654321654321')

    def test_project_spatial_relationship_create(self):
        self.generic_test_project_relationship_create(
            'spatial', api2.SpatialRelationshipCreate)

    def test_project_party_relationship_create(self):
        self.generic_test_project_relationship_create(
            'party', api.PartyRelationshipCreate)

    def test_project_tenure_relationship_create(self):
        self.generic_test_project_relationship_create(
            'tenure', api.TenureRelationshipCreate)

    def test_project_spatial_relationship_detail(self):
        self.generic_test_project_relationship_detail(
            'spatial', api2.SpatialRelationshipDetail)

    def test_project_party_relationship_detail(self):
        self.generic_test_project_relationship_detail(
            'party', api.PartyRelationshipDetail)

    def test_project_tenure_relationship_detail(self):
        self.generic_test_project_relationship_detail(
            'tenure', api.TenureRelationshipDetail)
