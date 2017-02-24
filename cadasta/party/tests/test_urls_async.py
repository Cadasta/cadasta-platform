from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from ..views import async


class PartyRelationshipUrlsTest(TestCase):
    def test_relationship_detail(self):
        url = reverse('async:party:relationship_detail',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'relationship': 'xyz456'})
        assert (url ==
                '/async/organizations/org-slug/projects/proj-slug/'
                'records/relationship/xyz456/')

        resolved = resolve(
            '/async/organizations/org-slug/projects/proj-slug/'
            'records/relationship/xyz456/')
        assert (resolved.func.__name__ ==
                async.PartyRelationshipDetail.__name__)
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['relationship'] == 'xyz456'

    def test_relationship_edit(self):
        url = reverse('async:party:relationship_edit',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'relationship': 'xyz456'})
        assert (url ==
                '/async/organizations/org-slug/projects/proj-slug/'
                'records/relationship/xyz456/edit/')

        resolved = resolve(
            '/async/organizations/org-slug/projects/proj-slug/'
            'records/relationship/xyz456/edit/')
        assert (resolved.func.__name__ ==
                async.PartyRelationshipEdit.__name__)
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['relationship'] == 'xyz456'

    def test_relationship_delete(self):
        url = reverse('async:party:relationship_delete',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'relationship': 'xyz456'})
        assert (url ==
                '/async/organizations/org-slug/projects/proj-slug/'
                'records/relationship/xyz456/delete/')

        resolved = resolve(
            '/async/organizations/org-slug/projects/proj-slug/'
            'records/relationship/xyz456/delete/')
        assert (resolved.func.__name__ ==
                async.PartyRelationshipDelete.__name__)
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['relationship'] == 'xyz456'

    def test_relationship_resources_new(self):
        url = reverse('async:party:relationship_resource_new',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'relationship': 'xyz456'})
        assert (url ==
                '/async/organizations/org-slug/projects/proj-slug/'
                'records/relationship/xyz456/resources/new/')

        resolved = resolve(
            '/async/organizations/org-slug/projects/proj-slug/'
            'records/relationship/xyz456/resources/new/')
        assert (resolved.func.__name__ ==
                async.PartyRelationshipResourceNew.__name__)
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['relationship'] == 'xyz456'

    def test_relationship_resources_add(self):
        url = reverse('async:party:relationship_resource_add',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'relationship': 'xyz456'})
        assert (url ==
                '/async/organizations/org-slug/projects/proj-slug/'
                'records/relationship/xyz456/resources/add/')

        resolved = resolve(
            '/async/organizations/org-slug/projects/proj-slug/'
            'records/relationship/xyz456/resources/add/')
        assert (resolved.func.__name__ ==
                async.PartyRelationshipResourceAdd.__name__)
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['relationship'] == 'xyz456'
