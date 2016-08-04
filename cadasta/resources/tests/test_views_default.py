import copy
import json
import os
import pytest
from django.http import Http404
from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse

from buckets.test.storage import FakeS3Storage
from tutelary.models import Policy, assign_user_policies
from skivvy import ViewTestCase

from core.tests.utils.cases import UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from organization.tests.factories import ProjectFactory
from spatial.tests.factories import SpatialUnitFactory
from party.tests.factories import PartyFactory, TenureRelationshipFactory
from accounts.tests.factories import UserFactory
from resources.models import Resource
from ..models import ContentObject
from ..views import default
from ..forms import ResourceForm, AddResourceFromLibraryForm
from .factories import ResourceFactory
from .utils import clear_temp  # noqa

path = os.path.dirname(settings.BASE_DIR)
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
        }
    ]
}


def assign_permissions(user, add_pols=None):
    additional_clauses = copy.deepcopy(clauses)
    if add_pols:
        additional_clauses['clause'] += add_pols

    policy = Policy.objects.create(
            name='allow',
            body=json.dumps(additional_clauses))
    assign_user_policies(user, policy)


@pytest.mark.usefixtures('make_dirs')
class ProjectResourcesTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ProjectResources
    template = 'resources/project_list.html'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.resources = ResourceFactory.create_batch(
            2, content_object=self.project, project=self.project)
        self.denied = ResourceFactory.create(content_object=self.project,
                                             project=self.project)
        ResourceFactory.create()

        self.user = UserFactory.create()
        assign_permissions(self.user, [
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

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def setup_template_context(self, resources=None):
        if resources is None:
            resources = Resource.objects.filter(
                project=self.project,
                archived=False).exclude(pk=self.denied.pk)

        resource_list = []
        if len(resources) > 0:
            object_id = resources[0].project.id
            attachments = ContentObject.objects.filter(object_id=object_id)
            attachment_id_dict = {x.resource.id: x.id for x in attachments}
            for resource in resources:
                resource_list.append(resource)
                attachment_id = attachment_id_dict.get(resource.id, None)
                setattr(resource, 'attachment_id', attachment_id)

        resource_count = self.project.resource_set.filter(
            archived=False).count()

        return {
            'object_list': resources,
            'object': self.project,
            'has_unattached_resources': (
                resource_count > 0 and
                resource_count != self.project.resources.count()
            ),
            'resource_list': resource_list,
        }

    def test_get_list(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_list_with_archived_resource(self):
        ResourceFactory.create(project=self.project, archived=True)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_list_with_unattached_resource_using_nonunarchiver(self):
        ResourceFactory.create(project=self.project)
        resources = Resource.objects.filter(project=self.project).exclude(
                                            pk=self.denied.pk)
        response = self.request(user=self.user)
        assert response.status_code == 200
        context = self.setup_template_context(resources=resources)
        assert response.content == self.render_content(**context)

    def test_get_list_with_archived_resource_using_unarchiver(self):
        assign_permissions(self.user)
        ResourceFactory.create(project=self.project, archived=True)
        resources = Resource.objects.filter(project=self.project)
        response = self.request(user=self.user)
        context = self.setup_template_context(resources=resources)
        assert response.content == self.render_content(**context)

    def test_get_with_unauthorized_user(self):
        response = self.request(user=UserFactory.create())
        assert response.status_code == 200
        context = self.setup_template_context(resources=[])
        assert response.content == self.render_content(**context)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_get_non_existent_project(self):
        with pytest.raises(Http404):
            self.request(user=self.user,
                         url_kwargs={'organization': 'some-org',
                                     'project': 'some-project'})


@pytest.mark.usefixtures('make_dirs')
class ProjectResourcesAddTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ProjectResourcesAdd
    template = 'resources/project_add_existing.html'
    success_url_name = 'resources:project_list'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.attached = ResourceFactory.create(project=self.project,
                                               content_object=self.project)
        self.unattached = ResourceFactory.create(project=self.project)

        self.user = UserFactory.create()
        assign_permissions(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def setup_template_context(self):
        form = AddResourceFromLibraryForm(content_object=self.project,
                                          project_id=self.project.id)
        return {'object': self.project, 'form': form}

    def setup_post_data(self):
        return {
            self.attached.id: False,
            self.unattached.id: True,
        }

    def test_get_list(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthorized_user(self):
        response = self.request(user=UserFactory.create())
        assert response.status_code == 302
        assert ("You don't have permission to add resources."
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_get_non_existent_project(self):
        with pytest.raises(Http404):
            self.request(user=self.user,
                         url_kwargs={'organization': 'some-org',
                                     'project': 'some-project'})

    def test_update(self):
        project_resources = self.project.resources.all()
        response = self.request(method='POST', user=self.user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url
        assert len(project_resources) == 2
        assert self.attached in project_resources
        assert self.unattached in project_resources

    def test_update_with_custom_redirect(self):
        project_resources = self.project.resources.all()
        response = self.request(method='POST', user=self.user,
                                get_data={'next': '/organizations/'})
        assert response.status_code == 302
        assert response.location == '/organizations/#resources'
        assert len(project_resources) == 2
        assert self.attached in project_resources
        assert self.unattached in project_resources

    def test_post_with_unauthorized_user(self):
        response = self.request(method='POST', user=UserFactory.create())
        assert ("You don't have permission to add resources."
                in response.messages)
        assert self.project.resources.count() == 1
        assert self.project.resources.first() == self.attached

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert self.project.resources.count() == 1
        assert self.project.resources.first() == self.attached


@pytest.mark.usefixtures('clear_temp')
@pytest.mark.usefixtures('make_dirs')
class ProjectResourcesNewTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ProjectResourcesNew
    template = 'resources/project_add_new.html'
    success_url_name = 'resources:project_list'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.user = UserFactory.create()
        assign_permissions(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def setup_template_context(self):
        form = ResourceForm()
        return {'object': self.project, 'form': form}

    def setup_post_data(self):
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/image.jpg', 'rb').read()
        file_name = storage.save('resources/image.jpg', file)

        return {
            'name': 'Some name',
            'description': '',
            'file': file_name,
            'original_file': 'image.png',
            'mime_type': 'image/jpeg'
        }

    def test_get_form(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_non_existent_project(self):
        with pytest.raises(Http404):
            self.request(user=self.user,
                         url_kwargs={'organization': 'some-org',
                                     'project': 'some-project'})

    def test_get_with_unauthorized_user(self):
        response = self.request(user=UserFactory.create())
        assert response.status_code == 302
        assert ("You don't have permission to add resources."
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_create(self):
        response = self.request(method='POST', user=self.user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url
        assert self.project.resources.count() == 1
        assert self.project.resources.first().name == 'Some name'

    def test_create_invalid_gpx(self):
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/mp3.xml', 'rb').read()
        file_name = storage.save('resources/mp3.xml', file)

        data = {
            'name': 'Some name',
            'description': '',
            'file': file_name,
            'original_file': 'image.png',
            'mime_type': 'text/xml'
        }
        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 200
        assert self.project.resources.count() == 0

    def test_create_with_custom_redirect(self):
        response = self.request(method='POST', user=self.user,
                                get_data={'next': '/organizations/'})
        assert response.status_code == 302
        assert response.location == '/organizations/#resources'
        assert self.project.resources.count() == 1
        assert self.project.resources.first().name == 'Some name'

    def test_post_with_unauthorized_user(self):
        response = self.request(method='POST', user=UserFactory.create())
        assert response.status_code == 302
        assert ("You don't have permission to add resources."
                in response.messages)
        assert self.project.resources.count() == 0

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert self.project.resources.count() == 0


@pytest.mark.usefixtures('make_dirs')
class ProjectResourcesDetailTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ProjectResourcesDetail
    template = 'resources/project_detail.html'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.org_slug = self.project.organization.slug
        self.resource = ResourceFactory.create(project=self.project)
        self.location = SpatialUnitFactory.create(project=self.project)
        self.party = PartyFactory.create(project=self.project)
        self.tenurerel = TenureRelationshipFactory.create(project=self.project)
        self.project_attachment = ContentObject.objects.create(
            resource_id=self.resource.id,
            content_object=self.project,
        )
        self.location_attachment = ContentObject.objects.create(
            resource_id=self.resource.id,
            content_object=self.location,
        )
        self.party_attachment = ContentObject.objects.create(
            resource_id=self.resource.id,
            content_object=self.party,
        )
        self.tenurerel_attachment = ContentObject.objects.create(
            resource_id=self.resource.id,
            content_object=self.tenurerel,
        )

        self.user = UserFactory.create()
        assign_permissions(self.user)

    def setup_template_context(self):
        return {
            'object': self.project,
            'resource': self.resource,
            'can_edit': True,
            'can_archive': True,
            'attachment_list': [
                {
                    'object': self.project,
                    'id': self.project_attachment.id,
                },
                {
                    'object': self.location,
                    'id': self.location_attachment.id,
                },
                {
                    'object': self.party,
                    'id': self.party_attachment.id,
                },
                {
                    'object': self.tenurerel,
                    'id': self.tenurerel_attachment.id,
                },
            ],
        }

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'resource': self.resource.id
        }

    def test_get_page(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_non_existent_project(self):
        with pytest.raises(Http404):
            self.request(user=self.user,
                         url_kwargs={'organization': 'some-org',
                                     'project': 'some-project'})

    def test_get_non_existent_resource(self):
        with pytest.raises(Http404):
            self.request(user=self.user, url_kwargs={'resource': 'abc123'})

    def test_get_with_unauthorized_user(self):
        response = self.request(user=UserFactory.create())
        assert response.status_code == 302
        assert ("You don't have permission to view this resource."
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location


@pytest.mark.usefixtures('make_dirs')
class ProjectResourcesEditTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ProjectResourcesEdit
    template = 'resources/edit.html'
    success_url_name = 'resources:project_detail'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.resource = ResourceFactory.create(content_object=self.project,
                                               project=self.project)

        self.user = UserFactory.create()
        assign_permissions(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'resource': self.resource.id
        }

    def setup_template_context(self):
        form = ResourceForm(instance=self.resource)
        return {
            'object': self.project,
            'form': form,
            'cancel_url': reverse(
                'resources:project_detail',
                kwargs={
                    'organization': self.project.organization.slug,
                    'project': self.project.slug,
                    'resource': self.resource.id,
                }
            )
        }

    def setup_post_data(self):
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/image.jpg', 'rb').read()
        file_name = storage.save('resources/image.jpg', file)
        return {
            'name': 'Some name',
            'description': '',
            'file': file_name,
            'original_file': 'image.png',
            'mime_type': 'image/jpeg'
        }

    def test_get_form(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_form_with_next_query_parameter(self):
        response = self.request(user=self.user,
                                get_data={'next': '/organizations/'})
        assert response.status_code == 200
        assert response.content == self.render_content(
            cancel_url='/organizations/#resources')

    def test_get_form_with_location_next_query_parameter(self):
        url = ('https://example.com/organizations/sample-org/'
               'projects/sample-proj/records/'
               'locations/jvzsiszjzrbpecm69549u2z5/')
        response = self.request(user=self.user, get_data={'next': url})
        assert response.status_code == 200
        assert response.content == self.render_content(
            cancel_url=url + '#resources')

    def test_get_non_existent_project(self):
        with pytest.raises(Http404):
            self.request(user=self.user,
                         url_kwargs={'organization': 'some-org',
                                     'project': 'some-project'})

    def test_get_non_existent_resource(self):
        with pytest.raises(Http404):
            self.request(user=self.user, url_kwargs={'resource': 'abc123'})

    def test_get_with_unauthorized_user(self):
        response = self.request(user=UserFactory.create())
        assert response.status_code == 302
        assert ("You don't have permission to edit this resource."
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_update(self):
        response = self.request(method='POST', user=self.user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url
        assert self.project.resources.count() == 1
        assert self.project.resources.first().name == 'Some name'

    def test_update_with_custom_redirect(self):
        get = {'next': 'http://example.com/'}
        response = self.request(method='POST', user=self.user, get_data=get)
        assert response.status_code == 302
        assert response.location == 'http://example.com/#resources'
        assert self.project.resources.count() == 1
        assert self.project.resources.first().name == 'Some name'

    def test_post_with_unauthorized_user(self):
        response = self.request(method='POST', user=UserFactory.create())
        assert response.status_code == 302
        assert ("You don't have permission to edit this resource."
                in response.messages)
        assert self.project.resources.count() == 1
        assert self.project.resources.first().name != 'Some name'

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert self.project.resources.count() == 1
        assert self.project.resources.first().name != 'Some name'


@pytest.mark.usefixtures('make_dirs')
class ResourceArchiveTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ResourceArchive
    template = 'resources:project_list'
    success_url_name = 'resources:project_detail'

    def setup_models(self):
        self.user = UserFactory.create()
        self.project = ProjectFactory.create()
        self.resource = ResourceFactory.create(content_object=self.project,
                                               project=self.project)
        assign_permissions(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'resource': self.resource.id
        }

    def test_archive(self):
        response = self.request(user=self.user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url

        self.resource.refresh_from_db()
        assert self.resource.archived is True

    def test_archive_with_custom_redirect(self):
        response = self.request(user=self.user,
                                get_data={'next': '/dashboard/'})
        assert response.status_code == 302
        assert response.location == '/dashboard/#resources'

        self.resource.refresh_from_db()
        assert self.resource.archived is True

    def test_archive_with_no_unarchive_permission(self):
        additional_clauses = copy.deepcopy(clauses)
        additional_clauses['clause'] += [
            {
                'effect': 'deny',
                'object': ['resource/*/*/*'],
                'action': ['resource.unarchive'],
            },
        ]
        policy = Policy.objects.create(
            name='allow',
            body=json.dumps(additional_clauses))
        assign_user_policies(self.user, policy)
        expected_success_url = reverse(
            'resources:project_list',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug,
            }
        )
        response = self.request(user=self.user)
        assert response.status_code == 302
        assert response.location == expected_success_url

        self.resource.refresh_from_db()
        assert self.resource.archived is True

    def test_archive_with_project_does_not_exist(self):
        with pytest.raises(Http404):
            self.request(user=self.user,
                         url_kwargs={'organization': 'some-org',
                                     'project': 'some-project'})

        self.resource.refresh_from_db()
        assert self.resource.archived is False

    def test_archive_resource_does_not_exist(self):
        with pytest.raises(Http404):
            self.request(user=self.user, url_kwargs={'resource': 'abc123'})

    def test_archive_with_unauthorized_user(self):
        response = self.request(user=UserFactory.create())
        assert response.status_code == 302
        assert ("You don't have permission to delete this resource."
                in response.messages)

        self.resource.refresh_from_db()
        assert self.resource.archived is False

    def test_archive_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

        self.resource.refresh_from_db()
        assert self.resource.archived is False


@pytest.mark.usefixtures('make_dirs')
class ResourceUnArchiveTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ResourceUnarchive
    template = 'resources:project_list'
    success_url_name = 'resources:project_detail'

    def setup_models(self):
        self.user = UserFactory.create()
        self.project = ProjectFactory.create()
        self.resource = ResourceFactory.create(content_object=self.project,
                                               project=self.project,
                                               archived=True)
        assign_permissions(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'resource': self.resource.id
        }

    def test_unarchive(self):
        response = self.request(user=self.user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url

        self.resource.refresh_from_db()
        assert self.resource.archived is False

    def test_unarchive_with_project_does_not_exist(self):
        with pytest.raises(Http404):
            self.request(user=self.user,
                         url_kwargs={'organization': 'some-org',
                                     'project': 'some-project'})

        self.resource.refresh_from_db()
        assert self.resource.archived is True

    def test_unarchive_resource_does_not_exist(self):
        with pytest.raises(Http404):
            self.request(user=self.user, url_kwargs={'resource': 'abc123'})

    def test_unarchive_with_unauthorized_user(self):
        with pytest.raises(Http404):
            self.request(user=UserFactory.create())
        self.resource.refresh_from_db()
        assert self.resource.archived is True

    def test_unarchive_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

        self.resource.refresh_from_db()
        assert self.resource.archived is True


@pytest.mark.usefixtures('make_dirs')
class ResourceDetachTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ResourceDetach
    success_url_name = 'resources:project_list'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.location = SpatialUnitFactory.create(project=self.project)
        self.resource = ResourceFactory.create(project=self.project)
        self.project_attachment = ContentObject.objects.create(
            resource_id=self.resource.id,
            content_object=self.project,
        )
        self.location_attachment = ContentObject.objects.create(
            resource_id=self.resource.id,
            content_object=self.location,
        )

        self.user = UserFactory.create()
        assign_permissions(self.user)

    def setup_post_data(self):
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/image.jpg', 'rb').read()
        file_name = storage.save('resources/image.jpg', file)

        return {
            'name': 'Some name',
            'description': '',
            'file': file_name,
            'original_file': 'image.png',
            'mime_type': 'image/jpeg'
        }

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'resource': self.resource.id,
            'attachment': self.project_attachment.id
        }

    def setup_success_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def refresh_objects_from_db(self):
        self.resource.refresh_from_db()
        self.project.refresh_from_db()
        self.project.reload_resources()
        self.location.refresh_from_db()
        self.location.reload_resources()

    def test_detach_from_project(self):
        response = self.request(method='POST', user=self.user)
        assert response.status_code == 302
        assert self.expected_success_url in response.location
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 1
        assert self.project.resources.count() == 0
        location_resources = self.location.resources
        assert location_resources.count() == 1
        assert location_resources.first() == self.resource

    def test_detach_from_location(self):
        response = self.request(
            method='POST',
            user=self.user,
            url_kwargs={'attachment': self.location_attachment.id})
        assert response.status_code == 302
        assert self.expected_success_url in response.location
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 1
        assert self.location.resources.count() == 0
        project_resources = self.project.resources
        assert project_resources.count() == 1
        assert project_resources.first() == self.resource

    def test_detach_with_custom_redirect(self):
        response = self.request(method='POST', user=self.user,
                                get_data={'next': '/dashboard/'})
        assert response.status_code == 302
        assert '/dashboard/#resources' in response.location
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 1
        assert self.project.resources.count() == 0
        location_resources = self.location.resources
        assert location_resources.count() == 1
        assert location_resources.first() == self.resource

    def test_detach_with_nonexistent_project(self):
        with pytest.raises(Http404):
            self.request(method='POST', user=self.user,
                         url_kwargs={'organization': 'some-org',
                                     'project': 'some-project'})

        self.refresh_objects_from_db()
        assert self.resource.num_entities == 2
        assert self.project.resources.count() == 1
        assert self.location.resources.count() == 1

    def test_detach_with_nonexistent_resource(self):
        with pytest.raises(Http404):
            self.request(method='POST', user=self.user,
                         url_kwargs={'resource': 'abc123'})
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 2
        assert self.project.resources.count() == 1
        assert self.location.resources.count() == 1

    def test_detach_with_nonexistent_attachment(self):
        with pytest.raises(Http404):
            self.request(method='POST', user=self.user,
                         url_kwargs={'attachment': 'abc123'})
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 2
        assert self.project.resources.count() == 1
        assert self.location.resources.count() == 1

    def test_detach_with_unauthorized_user(self):
        response = self.request(method='POST', user=UserFactory.create())
        assert ("You don't have permission to edit this resource."
                in response.messages)
        assert response.status_code == 302
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 2
        assert self.project.resources.count() == 1
        assert self.location.resources.count() == 1

    def test_detach_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 2
        assert self.project.resources.count() == 1
        assert self.location.resources.count() == 1
