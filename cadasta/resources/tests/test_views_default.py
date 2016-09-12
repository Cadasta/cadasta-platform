import copy
import json
import os
import pytest
from django.http import HttpRequest, Http404
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.api import get_messages

from buckets.test.storage import FakeS3Storage
from tutelary.models import Policy, assign_user_policies

from core.tests.base_test_case import UserTestCase
from core.tests.util import make_dirs  # noqa
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
            'action': ['resource.*'],
        },
        {
            'effect': 'allow',
            'object': ['resource/*/*/*'],
            'action': ['resource.*'],
        },
    ],
}


@pytest.mark.usefixtures('make_dirs')
class ProjectResourcesTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        self.resources = ResourceFactory.create_batch(
            2, content_object=self.project, project=self.project)
        self.denied = ResourceFactory.create(content_object=self.project,
                                             project=self.project)
        ResourceFactory.create()

        self.view = default.ProjectResources.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        self.user = UserFactory.create()

        additional_clauses = copy.deepcopy(clauses)
        additional_clauses['clause'] += [
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
        ]

        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(additional_clauses))
        assign_user_policies(self.user, self.policy)

    def _get(self, user=None, status=None, resources=None):
        if user is None:
            user = self.user
            Policy.objects.get(name='default')
        if resources is None:
            resources = self.resources

        setattr(self.request, 'user', user)
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        response = self.view(self.request,
                             organization=self.project.organization.slug,
                             project=self.project.slug)

        if status is not None:
            assert response.status_code == status

        if response.status_code == 200:
            content = response.render().content.decode('utf-8')

            resource_list = []
            if len(resources) > 0:
                object_id = resources[0].project.id
                attachments = ContentObject.objects.filter(object_id=object_id)
                attachment_id_dict = {x.resource.id: x.id for x in attachments}
                for resource in resources:
                    resource_list.append(resource)
                    attachment_id = attachment_id_dict.get(resource.id, None)
                    setattr(resource, 'attachment_id', attachment_id)

            resource_set = self.project.resource_set.filter(archived=False)
            expected = render_to_string(
                'resources/project_list.html',
                {
                    'object_list': resources,
                    'object': self.project,
                    'has_unattached_resources': (
                        resource_set.exists() and
                        resource_set.count() != self.project.resources.count()
                    ),
                    'resource_list': resource_list,
                },
                request=self.request
            )
            assert expected == content
        return response

    def test_get_list(self):
        resources = Resource.objects.filter(project=self.project,
                                            archived=False).exclude(
                                            pk=self.denied.pk)
        self._get(status=200, resources=resources)

    def test_get_list_with_unattached_resource_using_nonunarchiver(self):
        ResourceFactory.create(project=self.project)
        resources = Resource.objects.filter(project=self.project).exclude(
                                            pk=self.denied.pk)
        self._get(status=200, resources=resources)

    def test_get_list_with_archived_resource(self):
        ResourceFactory.create(project=self.project, archived=True)
        resources = Resource.objects.filter(project=self.project,
                                            archived=False).exclude(
                                            pk=self.denied.pk)
        self._get(status=200, resources=resources)

    def test_get_list_with_archived_resource_using_unarchiver(self):
        unarchiver = UserFactory.create()
        policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))
        assign_user_policies(unarchiver, policy)
        ResourceFactory.create(project=self.project, archived=True)
        resources = Resource.objects.filter(project=self.project)
        self._get(status=200, user=unarchiver, resources=resources)

    def test_get_with_unauthorized_user(self):
        self._get(status=200, user=UserFactory.create(), resources=[])

    def test_get_with_unauthenticated_user(self):
        response = self._get(status=302, user=AnonymousUser())
        assert '/account/login/' in response['location']

    def test_get_non_existent_project(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(self.request,
                      organization='some-org', project='some-project')


@pytest.mark.usefixtures('make_dirs')
class ProjectResourcesAddTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        self.attached = ResourceFactory.create(project=self.project,
                                               content_object=self.project)
        self.unattached = ResourceFactory.create(project=self.project)

        self.view = default.ProjectResourcesAdd.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        self.user = UserFactory.create()

        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        assign_user_policies(self.user, self.policy)

    def _get(self, user=None, status=None):
        if user is None:
            user = self.user

        setattr(self.request, 'user', user)
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        response = self.view(self.request,
                             organization=self.project.organization.slug,
                             project=self.project.slug)

        if status is not None:
            assert response.status_code == status

        if response.status_code == 200:
            content = response.render().content.decode('utf-8')
            form = AddResourceFromLibraryForm(content_object=self.project,
                                              project_id=self.project.id)
            expected = render_to_string(
                'resources/project_add_existing.html',
                {'object': self.project, 'form': form},
                request=self.request
            )
            assert expected == content
        return response

    def _post(self, user=None, status=None, expected_redirect=None):
        data = {
            self.attached.id: False,
            self.unattached.id: True,
        }

        if user is None:
            user = self.user

        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', data)
        setattr(self.request, 'user', user)
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        response = self.view(self.request,
                             organization=self.project.organization.slug,
                             project=self.project.slug)

        if status is not None:
            assert response.status_code == status
        if expected_redirect:
            assert expected_redirect in response['location']

    def test_get_list(self):
        self._get(status=200)

    def test_get_with_unauthorized_user(self):
        self._get(status=302, user=UserFactory.create())
        assert ("You don't have permission to add resources."
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self._get(status=302, user=AnonymousUser())
        assert '/account/login/' in response['location']

    def test_get_non_existent_project(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(self.request,
                      organization='some-org', project='some-project')

    def test_update(self):
        redirect_url = reverse(
            'resources:project_list',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug
            }
        )
        self._post(status=302, expected_redirect=redirect_url)
        project_resources = self.project.resources.all()
        assert len(project_resources) == 2
        assert self.attached in project_resources
        assert self.unattached in project_resources

    def test_update_with_custom_redirect(self):
        setattr(self.request, 'GET', {'next': '/organizations/'})
        self._post(status=302, expected_redirect='/organizations/#resources')
        project_resources = self.project.resources.all()
        assert len(project_resources) == 2
        assert self.attached in project_resources
        assert self.unattached in project_resources

    def test_post_with_unauthorized_user(self):
        self._post(status=302, user=UserFactory.create())
        assert ("You don't have permission to add resources."
                in [str(m) for m in get_messages(self.request)])
        assert self.project.resources.count() == 1
        assert self.project.resources.first() == self.attached

    def test_post_with_unauthenticated_user(self):
        self._post(status=302, user=AnonymousUser(),
                   expected_redirect='/account/login/')
        assert self.project.resources.count() == 1
        assert self.project.resources.first() == self.attached


@pytest.mark.usefixtures('clear_temp')
@pytest.mark.usefixtures('make_dirs')
class ProjectResourcesNewTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()

        self.view = default.ProjectResourcesNew.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        self.user = UserFactory.create()

        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        assign_user_policies(self.user, self.policy)

    def _get(self, user=None, status=None):
        if user is None:
            user = self.user

        setattr(self.request, 'user', user)
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        response = self.view(self.request,
                             organization=self.project.organization.slug,
                             project=self.project.slug)

        if status is not None:
            assert response.status_code == status

        if response.status_code == 200:
            content = response.render().content.decode('utf-8')
            form = ResourceForm()
            expected = render_to_string(
                'resources/project_add_new.html',
                {'object': self.project, 'form': form},
                request=self.request
            )
            assert expected == content
        return response

    def _post(self, user=None, status=None, expected_redirect=None):
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/image.jpg', 'rb').read()
        file_name = storage.save('resources/image.jpg', file)

        self.data = {
            'name': 'Some name',
            'description': '',
            'file': file_name,
            'original_file': 'image.png',
            'mime_type': 'image/jpeg'
        }

        if user is None:
            user = self.user

        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', self.data)
        setattr(self.request, 'user', user)
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        response = self.view(self.request,
                             organization=self.project.organization.slug,
                             project=self.project.slug)

        if status is not None:
            assert response.status_code == status
        if expected_redirect:
            assert expected_redirect in response['location']

    def _post_invalid(self, user=None, status=None, expected_redirect=None):
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/mp3.xml', 'rb').read()
        file_name = storage.save('resources/mp3.xml', file)

        self.data = {
            'name': 'Some name',
            'description': '',
            'file': file_name,
            'original_file': 'image.png',
            'mime_type': 'text/xml'
        }

        if user is None:
            user = self.user

        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', self.data)
        setattr(self.request, 'user', user)
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        response = self.view(self.request,
                             organization=self.project.organization.slug,
                             project=self.project.slug)

        if status is not None:
            assert response.status_code == status
        if expected_redirect:
            assert expected_redirect in response['location']

    def test_get_form(self):
        self._get(status=200)

    def test_get_non_existent_project(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(self.request,
                      organization='some-org', project='some-project')

    def test_get_with_unauthorized_user(self):
        self._get(status=302, user=UserFactory.create())
        assert ("You don't have permission to add resources."
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self._get(status=302, user=AnonymousUser())
        assert '/account/login/' in response['location']

    def test_create(self):
        redirect_url = reverse(
            'resources:project_list',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug
            }
        )
        self._post(status=302, expected_redirect=redirect_url)
        assert self.project.resources.count() == 1
        assert self.project.resources.first().name == self.data['name']

    def test_create_invalid_gpx(self):
        self._post_invalid()
        assert self.project.resources.count() == 0

    def test_create_with_custom_redirect(self):
        setattr(self.request, 'GET', {'next': '/organizations/'})
        self._post(status=302, expected_redirect='/organizations/#resources')
        assert self.project.resources.count() == 1
        assert self.project.resources.first().name == self.data['name']

    def test_post_with_unauthorized_user(self):
        self._post(status=302, user=UserFactory.create())
        assert ("You don't have permission to add resources."
                in [str(m) for m in get_messages(self.request)])
        assert self.project.resources.count() == 0

    def test_post_with_unauthenticated_user(self):
        self._post(status=302,
                   user=AnonymousUser(),
                   expected_redirect='/account/login/')
        assert self.project.resources.count() == 0


@pytest.mark.usefixtures('make_dirs')
class ProjectResourcesDetailTest(UserTestCase):
    def setUp(self):
        super().setUp()
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

        self.view = default.ProjectResourcesDetail.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        self.user = UserFactory.create()

        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))
        assign_user_policies(self.user, self.policy)

    def _get(self, user=None, status=None):
        if user is None:
            user = self.user

        setattr(self.request, 'user', user)
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        response = self.view(self.request,
                             organization=self.org_slug,
                             project=self.project.slug,
                             resource=self.resource.id)

        if status is not None:
            assert response.status_code == status

        if response.status_code == 200:
            content = response.render().content.decode('utf-8')
            expected = render_to_string(
                'resources/project_detail.html',
                {
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
                },
                request=self.request
            )
            assert expected == content
        return response

    def test_get_page(self):
        self._get(status=200)

    def test_get_non_existent_project(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(self.request,
                      organization='some-org',
                      project='some-project',
                      resource=self.resource.id)

    def test_get_non_existent_resource(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(self.request,
                      organization=self.project.organization.slug,
                      project=self.project.slug,
                      resource='abc123')

    def test_get_with_unauthorized_user(self):
        self._get(status=302, user=UserFactory.create())
        assert ("You don't have permission to view this resource."
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self._get(status=302, user=AnonymousUser())
        assert '/account/login/' in response['location']


@pytest.mark.usefixtures('make_dirs')
class ProjectResourcesEditTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        self.resource = ResourceFactory.create(content_object=self.project,
                                               project=self.project)

        self.view = default.ProjectResourcesEdit.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        self.user = UserFactory.create()

        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))
        assign_user_policies(self.user, self.policy)

    def _get(self, user=None, status=None):
        if user is None:
            user = self.user

        setattr(self.request, 'user', user)
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        response = self.view(self.request,
                             organization=self.project.organization.slug,
                             project=self.project.slug,
                             resource=self.resource.id)

        if status is not None:
            assert response.status_code == status

        if response.status_code == 200:
            content = response.render().content.decode('utf-8')
            form = ResourceForm(instance=self.resource)
            cancel_url = self.request.GET.get('next', None)
            if cancel_url:
                cancel_url += '#resources'
            else:
                cancel_url = reverse(
                    'resources:project_detail',
                    kwargs={
                        'organization': self.project.organization.slug,
                        'project': self.project.slug,
                        'resource': self.resource.id,
                    }
                )
            expected = render_to_string(
                'resources/edit.html',
                {
                    'object': self.project,
                    'form': form,
                    'cancel_url': cancel_url,
                },
                request=self.request
            )
            assert expected == content
        return response

    def _post(self, user=None, status=None, expected_redirect=None, get=None):
        if user is None:
            user = self.user

        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/image.jpg', 'rb').read()
        file_name = storage.save('resources/image.jpg', file)
        self.data = {
            'name': 'Some name',
            'description': '',
            'file': file_name,
            'original_file': 'image.png',
            'mime_type': 'image/jpeg'
        }

        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', self.data)
        if get:
            setattr(self.request, 'GET', get)
        setattr(self.request, 'user', user)
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        response = self.view(self.request,
                             organization=self.project.organization.slug,
                             project=self.project.slug,
                             resource=self.resource.id)

        if status is not None:
            assert response.status_code == status
        if expected_redirect:
            assert expected_redirect in response['location']
        return response

    def test_get_form(self):
        self._get(status=200)

    def test_get_non_existent_project(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(self.request,
                      organization='some-org',
                      project='some-project',
                      resource=self.resource.id)

    def test_get_non_existent_resource(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(self.request,
                      organization=self.project.organization.slug,
                      project=self.project.slug,
                      resource='abc123')

    def test_get_with_unauthorized_user(self):
        self._get(status=302, user=UserFactory.create())
        assert ("You don't have permission to edit this resource."
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self._get(status=302, user=AnonymousUser())
        assert '/account/login/' in response['location']

    def test_update(self):
        redirect_url = reverse(
            'resources:project_detail',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug,
                'resource': self.resource.id,
            }
        )
        self._post(status=302, expected_redirect=redirect_url)
        assert self.project.resources.count() == 1
        assert self.project.resources.first().name == self.data['name']

    def test_update_with_custom_redirect(self):
        self._post(status=302,
                   expected_redirect='http://example.com/#resources',
                   get={'next': 'http://example.com/'})
        assert self.project.resources.count() == 1
        assert self.project.resources.first().name == self.data['name']

    def test_post_with_unauthorized_user(self):
        self._post(status=302, user=UserFactory.create())
        assert ("You don't have permission to edit this resource."
                in [str(m) for m in get_messages(self.request)])
        assert self.project.resources.count() == 1
        assert self.project.resources.first().name != self.data['name']

    def test_post_with_unauthenticated_user(self):
        response = self._post(status=302, user=AnonymousUser())
        assert '/account/login/' in response['location']
        assert self.project.resources.count() == 1
        assert self.project.resources.first().name != self.data['name']


@pytest.mark.usefixtures('make_dirs')
class ResourceArchiveTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.project = ProjectFactory.create()
        self.resource = ResourceFactory.create(content_object=self.project,
                                               project=self.project)

        self.view = default.ResourceArchive.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        self.redirect_url = reverse(
            'resources:project_detail',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug,
                'resource': self.resource.id,
            }
        )
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))
        assign_user_policies(self.user, self.policy)

    def _get(self, user=None, status=None, redirect_url=None):
        if not user:
            user = self.user

        setattr(self.request, 'user', user)

        response = self.view(self.request,
                             organization=self.project.organization.slug,
                             project=self.project.slug,
                             resource=self.resource.id)

        if status:
            assert response.status_code == status
        if redirect_url:
            assert redirect_url in response['location']
        return response

    def test_archive(self):
        self._get(status=302, redirect_url=self.redirect_url)

        self.resource.refresh_from_db()
        assert self.resource.archived is True

    def test_archive_with_custom_redirect(self):
        setattr(self.request, 'GET', {'next': '/dashboard/'})
        self._get(status=302, redirect_url='/dashboard/#resources')

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
        redirect_url = reverse(
            'resources:project_list',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug,
            }
        )
        self._get(status=302, redirect_url=redirect_url)

        self.resource.refresh_from_db()
        assert self.resource.archived is True

    def test_archive_with_project_does_not_exist(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(self.request,
                      organization='some-org',
                      project='some-project',
                      resource=self.resource.id)

        self.resource.refresh_from_db()
        assert self.resource.archived is False

    def test_archive_resource_does_not_exist(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(self.request,
                      organization=self.project.organization.slug,
                      project=self.project.slug,
                      resource='abc123')

    def test_archive_with_unauthorized_user(self):
        self._get(status=302, user=UserFactory.create())
        assert ("You don't have permission to delete this resource."
                in [str(m) for m in get_messages(self.request)])

        self.resource.refresh_from_db()
        assert self.resource.archived is False

    def test_archive_with_unauthenticated_user(self):
        response = self._get(status=302, user=AnonymousUser())
        assert '/account/login/' in response['location']

        self.resource.refresh_from_db()
        assert self.resource.archived is False


@pytest.mark.usefixtures('make_dirs')
class ResourceUnArchiveTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.project = ProjectFactory.create()
        self.resource = ResourceFactory.create(content_object=self.project,
                                               project=self.project,
                                               archived=True)

        self.view = default.ResourceUnarchive.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        self.redirect_url = reverse(
            'resources:project_detail',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug,
                'resource': self.resource.id,
            }
        )
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))
        assign_user_policies(self.user, self.policy)

    def _get(self, user=None, status=None, redirect_url=None):
        if not user:
            user = self.user

        setattr(self.request, 'user', user)

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        response = self.view(self.request,
                             organization=self.project.organization.slug,
                             project=self.project.slug,
                             resource=self.resource.id)

        if status:
            assert response.status_code == status
        if redirect_url:
            assert redirect_url in response['location']

        return response

    def test_unarchive(self):
        self._get(status=302, redirect_url=self.redirect_url)

        self.resource.refresh_from_db()
        assert self.resource.archived is False

    def test_unarchive_with_project_does_not_exist(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(self.request,
                      organization='some-org',
                      project='some-project',
                      resource=self.resource.id)

        self.resource.refresh_from_db()
        assert self.resource.archived is True

    def test_unarchive_resource_does_not_exist(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(self.request,
                      organization=self.project.organization.slug,
                      project=self.project.slug,
                      resource='abc123')

    def test_unarchive_with_unauthorized_user(self):
        setattr(self.request, 'user', UserFactory.create())
        with pytest.raises(Http404):
            self.view(self.request,
                      organization=self.project.organization.slug,
                      project=self.project.slug,
                      resource=self.resource.id)

        self.resource.refresh_from_db()
        assert self.resource.archived is True

    def test_unarchive_with_unauthenticated_user(self):
        response = self._get(status=302, user=AnonymousUser())
        assert '/account/login/' in response['location']

        self.resource.refresh_from_db()
        assert self.resource.archived is True


@pytest.mark.usefixtures('make_dirs')
class ResourceDetachTest(UserTestCase):
    def setUp(self):
        super().setUp()

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
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))
        assign_user_policies(self.user, self.policy)

        self.view = default.ResourceDetach.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)
        self.redirect_url = reverse(
            'resources:project_list',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug
            }
        )

    def _post(self, attachment_id, user=None):
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/image.jpg', 'rb').read()
        file_name = storage.save('resources/image.jpg', file)
        self.data = {
            'name': 'Some name',
            'description': '',
            'file': file_name,
            'original_file': 'image.png',
            'mime_type': 'image/jpeg'
        }

        if user is None:
            user = self.user
        setattr(self.request, 'user', user)

        response = self.view(
            self.request,
            organization=self.project.organization.slug,
            project=self.project.slug,
            resource=self.resource.id,
            attachment=attachment_id,
        )
        return response

    def refresh_objects_from_db(self):
        self.resource.refresh_from_db()
        self.project.refresh_from_db()
        self.project.reload_resources()
        self.location.refresh_from_db()
        self.location.reload_resources()

    def test_detach_from_project(self):
        response = self._post(self.project_attachment.id)
        assert response.status_code == 302
        assert self.redirect_url in response['location']
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 1
        assert self.project.resources.count() == 0
        location_resources = self.location.resources
        assert location_resources.count() == 1
        assert location_resources.first() == self.resource

    def test_detach_from_location(self):
        response = self._post(self.location_attachment.id)
        assert response.status_code == 302
        assert self.redirect_url in response['location']
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 1
        assert self.location.resources.count() == 0
        project_resources = self.project.resources
        assert project_resources.count() == 1
        assert project_resources.first() == self.resource

    def test_detach_with_custom_redirect(self):
        setattr(self.request, 'GET', {'next': '/dashboard/'})
        response = self._post(self.project_attachment.id)
        assert response.status_code == 302
        assert '/dashboard/#resources' in response['location']
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 1
        assert self.project.resources.count() == 0
        location_resources = self.location.resources
        assert location_resources.count() == 1
        assert location_resources.first() == self.resource

    def test_detach_with_nonexistent_project(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(
                self.request,
                organization='some-org',
                project='some-project',
                resource=self.resource.id,
                attachment=self.project_attachment.id,
            )
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 2
        assert self.project.resources.count() == 1
        assert self.location.resources.count() == 1

    def test_detach_with_nonexistent_resource(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(
                self.request,
                organization=self.project.organization.slug,
                project=self.project.slug,
                resource='abc123',
                attachment=self.project_attachment.id,
            )
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 2
        assert self.project.resources.count() == 1
        assert self.location.resources.count() == 1

    def test_detach_with_nonexistent_attachment(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(
                self.request,
                organization=self.project.organization.slug,
                project=self.project.slug,
                resource=self.resource.id,
                attachment='abc123',
            )
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 2
        assert self.project.resources.count() == 1
        assert self.location.resources.count() == 1

    def test_detach_with_unauthorized_user(self):
        response = self._post(self.project_attachment.id,
                              user=UserFactory.create())
        assert ("You don't have permission to edit this resource."
                in [str(m) for m in get_messages(self.request)])
        assert response.status_code == 302
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 2
        assert self.project.resources.count() == 1
        assert self.location.resources.count() == 1

    def test_detach_with_unauthenticated_user(self):
        response = self._post(self.project_attachment.id, user=AnonymousUser())
        assert response.status_code == 302
        assert '/account/login/' in response['location']
        self.refresh_objects_from_db()
        assert self.resource.num_entities == 2
        assert self.project.resources.count() == 1
        assert self.location.resources.count() == 1
