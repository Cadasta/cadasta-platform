import copy
import json
import pytest

from django.test import TestCase
from skivvy import APITestCase

from tutelary.models import Policy

from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from core.tests.utils.files import make_dirs  # noqa
from organization.tests.factories import ProjectFactory
from accounts.tests.factories import UserFactory
from .factories import ResourceFactory
from ..views import api


clauses = {
    'clause': [
        {
            'effect': 'allow',
            'object': ['project/*/*'],
            'action': ['resource.*']
        },
        {
            'effect': 'allow',
            'object': ['resource/*/*/*'],
            'action': ['resource.*']
        },
    ],
}


def assign_policies(user, add_clauses=None):
    additional_clauses = copy.deepcopy(clauses)
    if add_clauses:
        additional_clauses['clause'] += add_clauses

    policy = Policy.objects.create(
            name='allow',
            body=json.dumps(additional_clauses))
    user.assign_policies(policy)


@pytest.mark.usefixtures('make_dirs')
class ProjectResourcesTest(APITestCase, UserTestCase,
                           FileStorageTestCase, TestCase):
    view_class = api.ProjectResources

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.resources = ResourceFactory.create_batch(
            2, content_object=self.project, project=self.project)
        self.denied = ResourceFactory.create(content_object=self.project,
                                             project=self.project)
        ResourceFactory.create()

        self.user = UserFactory.create()
        assign_policies(self.user, add_clauses=[
            {
                'effect': 'deny',
                'object': ['resource/*/*/' + self.denied.id],
                'action': ['resource.*'],
            },
            {
                'effect': 'deny',
                'object': ['resource/*/*/*'],
                'action': ['resource.unarchive'],
            },
        ])

        self.storage = self.get_storage()
        self.file = self.get_file(
            '/resources/tests/files/image.jpg', 'rb')
        self.file_name = self.storage.save('resources/image.jpg',
                                           self.file.read())
        self.file.close()

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def setup_post_data(self):
        return {
            'name': 'New resource',
            'description': '',
            'file': self.file_name,
            'original_file': 'image.png'
        }

    def test_list_resources(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content['results']) == 2

        returned_ids = [r['id'] for r in response.content['results']]
        assert all(res.id in returned_ids for res in self.resources)

    def test_get_full_list_organization_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'organization': 'abc'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_get_full_list_project_does_not_exist(self):
        response = self.request(user=self.user, url_kwargs={'project': 'abc'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_get_full_list_with_unauthorized_user(self):
        response = self.request(user=UserFactory.create())
        assert response.status_code == 200
        assert len(response.content['results']) == 0

    def test_add_resource(self):
        response = self.request(method='POST', user=self.user)
        assert response.status_code == 201
        assert self.project.resources.count() == 4

    def test_add_resource_with_unauthorized_user(self):
        response = self.request(method='POST', user=UserFactory.create())
        assert response.status_code == 403
        assert self.project.resources.count() == 3

    def test_add_existing_resource(self):
        new_resource = ResourceFactory.create()
        data = {'id': new_resource.id}
        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 201
        assert self.project.resources.count() == 4
        assert new_resource in self.project.resources

    def test_add_invalid_resource(self):
        data = {'name': ''}
        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 400
        assert self.project.resources.count() == 3
        assert 'This field may not be blank.' in response.content['name']

    def test_add_with_archived_project(self):
        data = {
            'name': 'New resource',
            'description': '',
            'file': self.file_name
        }
        self.project.archived = True
        self.project.save()

        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 403
        assert self.project.resources.count() == 3

    def test_search_for_file(self):
        prj = ProjectFactory.create()
        ResourceFactory.create_from_kwargs([
            {
                'content_object': prj,
                'project': prj,
                'original_file': 'my/image.png'
            },
            {
                'content_object': prj,
                'project': prj,
                'original_file': 'foo/an_image_thing.jpeg'
            },
            {
                'content_object': prj,
                'project': prj,
                'original_file': 'bar.png'
            }
        ])

        response = self.request(
            user=self.user,
            url_kwargs={'organization': prj.organization.slug,
                        'project': prj.slug},
            get_data={'search': 'image'})
        assert response.status_code == 200
        assert len(response.content['results']) == 2

    def test_filter_unarchived(self):
        prj = ProjectFactory.create()
        ResourceFactory.create_from_kwargs([
            {'content_object': prj, 'project': prj, 'archived': True},
            {'content_object': prj, 'project': prj, 'archived': True},
            {'content_object': prj, 'project': prj, 'archived': False},
        ])
        response = self.request(
            user=self.user,
            url_kwargs={'organization': prj.organization.slug,
                        'project': prj.slug},
            get_data={'archived': False})
        assert response.status_code == 200
        assert len(response.content['results']) == 1

    def test_filter_archived_with_nonunarchiver(self):
        prj = ProjectFactory.create()
        ResourceFactory.create_from_kwargs([
            {'content_object': prj, 'project': prj, 'archived': True},
            {'content_object': prj, 'project': prj, 'archived': True},
            {'content_object': prj, 'project': prj, 'archived': False},
        ])

        response = self.request(
            user=self.user,
            url_kwargs={'organization': prj.organization.slug,
                        'project': prj.slug},
            get_data={'archived': True})
        assert response.status_code == 200
        assert len(response.content['results']) == 0

    def test_filter_archived_with_unarchiver(self):
        prj = ProjectFactory.create()
        ResourceFactory.create_from_kwargs([
            {'content_object': prj, 'project': prj, 'archived': True},
            {'content_object': prj, 'project': prj, 'archived': True},
            {'content_object': prj, 'project': prj, 'archived': False},
        ])
        unarchiver = UserFactory.create()
        policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))
        unarchiver.assign_policies(policy)

        response = self.request(
            user=unarchiver,
            url_kwargs={'organization': prj.organization.slug,
                        'project': prj.slug},
            get_data={'archived': True})
        assert response.status_code == 200
        assert len(response.content['results']) == 2

    def test_ordering(self):
        prj = ProjectFactory.create()
        ResourceFactory.create_from_kwargs([
            {'content_object': prj, 'project': prj, 'name': 'A'},
            {'content_object': prj, 'project': prj, 'name': 'B'},
            {'content_object': prj, 'project': prj, 'name': 'C'},
        ])

        response = self.request(
            user=self.user,
            url_kwargs={'organization': prj.organization.slug,
                        'project': prj.slug},
            get_data={'ordering': 'name'})
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        names = [resource['name'] for resource in response.content['results']]
        assert(names == sorted(names))

    def test_reverse_ordering(self):
        prj = ProjectFactory.create()
        ResourceFactory.create_from_kwargs([
            {'content_object': prj, 'project': prj, 'name': 'A'},
            {'content_object': prj, 'project': prj, 'name': 'B'},
            {'content_object': prj, 'project': prj, 'name': 'C'},
        ])
        response = self.request(
            user=self.user,
            url_kwargs={'organization': prj.organization.slug,
                        'project': prj.slug},
            get_data={'ordering': '-name'})
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        names = [resource['name'] for resource in response.content['results']]
        assert(names == sorted(names, reverse=True))


@pytest.mark.usefixtures('make_dirs')
class ProjectResourcesDetailTest(APITestCase, UserTestCase, TestCase):
    view_class = api.ProjectResourcesDetail
    post_data = {'name': 'Updated'}

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.resource = ResourceFactory.create(content_object=self.project,
                                               project=self.project)
        self.user = UserFactory.create()
        assign_policies(self.user, add_clauses=[
            {
                'effect': 'deny',
                'object': ['resource/*/*/*'],
                'action': ['resource.unarchive'],
            },
        ])

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'resource': self.resource.id
        }

    def test_get_resource(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.resource.id

    def test_get_resource_with_unauthorized_user(self):
        response = self.request(user=UserFactory.create())
        assert response.status_code == 403
        assert 'id' not in response.content

    def test_get_resource_from_org_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'organization': 'some-org'})
        assert response.status_code == 404
        assert response.content['detail'] == "Not found."

    def test_get_resource_from_project_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'project': 'some-prj'})
        assert response.status_code == 404
        assert response.content['detail'] == "Not found."

    def test_get_resource_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'resource': 'abc123'})
        assert response.status_code == 404
        assert response.content['detail'] == "Not found."

    def test_update_resource(self):
        response = self.request(method='PATCH', user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.resource.id
        self.resource.refresh_from_db()
        assert self.resource.name == self.post_data['name']

    def test_PATCH_resource_with_unauthorized_user(self):
        response = self.request(method='PATCH', user=UserFactory.create())
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_PATCH_resource_with_anonymous_user(self):
        response = self.request(method='PATCH')
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_PUT_resource_with_unauthorized_user(self):
        response = self.request(method='PUT', user=UserFactory.create())
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_PUT_resource_with_anonymous_user(self):
        response = self.request(method='PUT')
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_update_invalid_resource(self):
        data = {'name': ''}
        response = self.request(method='PATCH', user=self.user, post_data=data)
        assert response.status_code == 400
        assert 'name' in response.content
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_update_with_archived_project(self):
        self.project.archived = True
        self.project.save()
        response = self.request(method='PATCH', user=UserFactory.create())
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_archive_resource(self):
        data = {'archived': True}
        response = self.request(method='PATCH', user=self.user, post_data=data)
        assert response.status_code == 200
        assert response.content['id'] == self.resource.id
        self.resource.refresh_from_db()
        assert self.resource.archived is True

    def test_archive_resource_with_unauthorized_user(self):
        data = {'archived': True}
        response = self.request(method='PATCH', user=UserFactory.create(),
                                post_data=data)
        assert response.status_code == 403
        assert 'id' not in response.content
        self.resource.refresh_from_db()
        assert self.resource.archived is False

    def test_unarchive_resource(self):
        self.resource.archived = True
        self.resource.save()
        data = {'archived': False}
        assign_policies(self.user)

        response = self.request(method='PATCH', user=self.user, post_data=data)
        assert response.status_code == 200
        assert response.content['id'] == self.resource.id
        self.resource.refresh_from_db()
        assert self.resource.archived is False

    def test_unarchive_resource_with_unauthorized_user(self):
        self.resource.archived = True
        self.resource.save()
        data = {'archived': False}
        response = self.request(method='PATCH', user=UserFactory.create(),
                                post_data=data)
        assert response.status_code == 404
        self.resource.refresh_from_db()
        assert self.resource.archived is True


@pytest.mark.usefixtures('make_dirs')
class ProjectSpatialResourcesTest(APITestCase, UserTestCase,
                                  FileStorageTestCase, TestCase):
    view_class = api.ProjectSpatialResources

    def setup_models(self):
        tracks = self.get_file('/resources/tests/files/tracks.gpx', 'rb')
        self.tracks_file = self.storage.save('resources/tracks.gpx',
                                             tracks.read())
        tracks.close()

        routes = self.get_file('/resources/tests/files/routes.gpx', 'rb')
        self.routes_file = self.storage.save('resources/routes.gpx',
                                             routes.read())
        routes.close()

        waypoints = self.get_file('/resources/tests/files/waypoints.gpx', 'rb')
        self.waypoints_file = self.storage.save(
            'resources/waypoints.gpx', waypoints.read())
        waypoints.close()

        self.project = ProjectFactory.create()

        # create non-spatial resources
        ResourceFactory.create_batch(
            2, content_object=self.project, project=self.project)

        # create attached spatial resource
        self.resource = ResourceFactory.create(
            content_object=self.project,
            project=self.project, file=self.tracks_file,
            original_file='tracks.gpx', mime_type='text/xml'
        )

        # unauthorized
        self.denied = ResourceFactory.create(
            content_object=self.project,
            project=self.project, file=self.routes_file,
            original_file='routes.gpx', mime_type='text/xml'
        )

        # create archived spatial resource
        ResourceFactory.create(
            content_object=self.project, archived=True,
            project=self.project, file=self.routes_file,
            original_file='routes.gpx', mime_type='text/xml'
        )

        # create unattached spatial resource
        ResourceFactory.create(
            content_object=None,
            project=self.project, file=self.waypoints_file,
            original_file='waypoints.gpx', mime_type='text/xml'
        )

        self.user = UserFactory.create()
        additional_clauses = [
            {
                'effect': 'deny',
                'object': ['resource/*/*/' + self.denied.id],
                'action': ['resource.*'],
            }
        ]
        assign_policies(self.user, add_clauses=additional_clauses)

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def test_list_spatial_resources(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        results = response.content['results']
        assert len(results) == 1
        assert results[0]['id'] == self.resource.id
        assert results[0]['spatial_resources'] is not None
        assert results[0]['spatial_resources'][0]['name'] == 'tracks'
        assert results[0]['spatial_resources'][0][
            'geom']['type'] == 'GeometryCollection'
        assert results[0]['spatial_resources'][0]['geom'][
            'geometries'][0]['type'] == 'MultiLineString'

    def test_list_spatial_resources_with_unauthorized_user(self):
        response = self.request(user=UserFactory.create())
        assert response.status_code == 200
        assert len(response.content['results']) == 0
        assert response.content['results'] == []


@pytest.mark.usefixtures('make_dirs')
class ProjectSpatialResourcesDetailTest(APITestCase, UserTestCase,
                                        FileStorageTestCase, TestCase):
    view_class = api.ProjectSpatialResourcesDetail
    post_data = {'name': 'Updated'}

    def setup_models(self):
        tracks = self.get_file('/resources/tests/files/tracks.gpx', 'rb')
        self.tracks_file = self.storage.save('resources/tracks.gpx',
                                             tracks.read())
        tracks.close()

        routes = self.get_file('/resources/tests/files/routes.gpx', 'rb')
        self.routes_file = self.storage.save('resources/routes.gpx',
                                             routes.read())
        routes.close()

        waypoints = self.get_file('/resources/tests/files/waypoints.gpx', 'rb')
        self.waypoints_file = self.storage.save(
            'resources/waypoints.gpx', waypoints.read())
        waypoints.close()

        self.project = ProjectFactory.create()

        # create non-spatial resources
        ResourceFactory.create_batch(
            2, content_object=self.project, project=self.project)

        # create attached spatial resource
        self.resource = ResourceFactory.create(
            content_object=self.project,
            project=self.project, file=self.tracks_file,
            original_file='tracks.gpx', mime_type='text/xml'
        )

        # unauthorized
        self.denied = ResourceFactory.create(
            content_object=self.project,
            project=self.project, file=self.routes_file,
            original_file='routes.gpx', mime_type='text/xml'
        )

        # create archived spatial resource
        ResourceFactory.create(
            content_object=self.project, archived=True,
            project=self.project, file=self.routes_file,
            original_file='routes.gpx', mime_type='text/xml'
        )

        # create unattached spatial resource
        ResourceFactory.create(
            content_object=None,
            project=self.project, file=self.waypoints_file,
            original_file='waypoints.gpx', mime_type='text/xml'
        )

        self.user = UserFactory.create()
        additional_clauses = [
            {
                'effect': 'deny',
                'object': ['resource/*/*/' + self.denied.id],
                'action': ['resource.*'],
            }
        ]
        assign_policies(self.user, add_clauses=additional_clauses)

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'resource': self.resource.id
        }

    def test_get_resource(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.resource.id

    def test_get_resource_with_unauthorized_user(self):
        response = self.request(user=UserFactory.create())
        assert response.status_code == 403
        assert 'id' not in response.content

    def test_get_resource_from_org_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'organization': 'some-org'})
        assert response.status_code == 404
        assert response.content['detail'] == "Not found."

    def test_get_resource_from_project_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'project': 'some-prj'})
        assert response.status_code == 404
        assert response.content['detail'] == "Not found."

    def test_get_resource_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'resource': 'abc123'})
        assert response.status_code == 404
        assert response.content['detail'] == "Not found."

    def test_update_resource(self):
        response = self.request(method='PATCH', user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.resource.id
        self.resource.refresh_from_db()
        assert self.resource.name == self.post_data['name']

    def test_PATCH_resource_with_unauthorized_user(self):
        response = self.request(method='PATCH', user=UserFactory.create())
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_PATCH_resource_with_anonymous_user(self):
        response = self.request(method='PATCH')
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_PUT_resource_with_unauthorized_user(self):
        response = self.request(method='PUT', user=UserFactory.create())
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_PUT_resource_with_anonymous_user(self):
        response = self.request(method='PUT')
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_update_invalid_resource(self):
        data = {'name': ''}
        response = self.request(method='PATCH', user=self.user, post_data=data)
        assert response.status_code == 400
        assert 'name' in response.content
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_update_with_archived_project(self):
        self.project.archived = True
        self.project.save()
        response = self.request(method='PATCH', user=UserFactory.create())
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_archive_resource(self):
        data = {'archived': True}
        response = self.request(method='PATCH', user=self.user, post_data=data)
        assert response.status_code == 200
        assert response.content['id'] == self.resource.id
        self.resource.refresh_from_db()
        assert self.resource.archived is True

    def test_archive_resource_with_unauthorized_user(self):
        data = {'archived': True}
        response = self.request(method='PATCH', user=UserFactory.create(),
                                post_data=data)
        assert response.status_code == 403
        assert 'id' not in response.content
        self.resource.refresh_from_db()
        assert self.resource.archived is False

    def test_unarchive_resource(self):
        self.resource.archived = True
        self.resource.save()
        data = {'archived': False}

        response = self.request(method='PATCH', user=self.user, post_data=data)
        assert response.status_code == 200
        assert response.content['id'] == self.resource.id
        self.resource.refresh_from_db()
        assert self.resource.archived is False

    def test_unarchive_resource_with_unauthorized_user(self):
        self.resource.archived = True
        self.resource.save()
        data = {'archived': False}
        response = self.request(method='PATCH', user=UserFactory.create(),
                                post_data=data)
        assert response.status_code == 404
        self.resource.refresh_from_db()
        assert self.resource.archived is True
