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
from accounts.tests.factories import UserFactory
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

        clauses['clause'].append({
            'effect': 'deny',
            'object': ['resource/*/*/' + self.denied.id],
            'action': ['resource.*']
        })

        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))
        assign_user_policies(self.user, self.policy)

    def _get(self, user=None, status=None, resources=None):
        if user is None:
            user = self.user
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
            expected = render_to_string(
                'resources/project_list.html',
                {
                    'object_list': resources,
                    'object': self.project,
                    'project_has_resources': (
                        self.project.resource_set.exists()),
                },
                request=self.request
            )
            assert expected == content
        return response

    def test_get_list(self):
        self._get(status=200)

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
        self.assigned = ResourceFactory.create(project=self.project,
                                               content_object=self.project)
        self.unassigned = ResourceFactory.create(project=self.project)

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
            self.assigned.id: False,
            self.unassigned.id: True,
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
        assert self.project.resources.count() == 1
        assert self.project.resources.first() == self.unassigned

    def test_post_with_unauthorized_user(self):
        self._post(status=302, user=UserFactory.create())
        assert ("You don't have permission to add resources."
                in [str(m) for m in get_messages(self.request)])
        assert self.project.resources.count() == 1
        assert self.project.resources.first() == self.assigned

    def test_post_with_unauthenticated_user(self):
        self._post(status=302, user=AnonymousUser(),
                   expected_redirect='/account/login/')
        assert self.project.resources.count() == 1
        assert self.project.resources.first() == self.assigned


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
        self.resource = ResourceFactory.create(content_object=self.project,
                                               project=self.project)

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
                             organization=self.project.organization.slug,
                             project=self.project.slug,
                             resource=self.resource.id)

        if status is not None:
            assert response.status_code == status

        if response.status_code == 200:
            content = response.render().content.decode('utf-8')
            expected = render_to_string(
                'resources/project_detail.html',
                {'object_list': self.project.resources,
                 'object': self.project,
                 'resource': self.resource},
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
                    'resources:project_list',
                    kwargs={
                        'organization': self.project.organization.slug,
                        'project': self.project.slug
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

    def test_get_form_with_next_query_parameter(self):
        self.request.GET['next'] = '/organizations/'
        self._get(status=200)

    def test_get_form_with_location_next_query_parameter(self):
        url = ('https://example.com/organizations/sample-org/'
               'projects/sample-proj/records/'
               'locations/jvzsiszjzrbpecm69549u2z5/')
        self.request.GET['next'] = url
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
            'resources:project_list',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug
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
            'resources:project_list',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug
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
        assert ("You don't have permission to archive this resource."
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
            'resources:project_list',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug
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

    def test_archive_project_does_not_exist(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(self.request,
                      organization=self.project.organization.slug,
                      project=self.project.slug,
                      resource='abc123')

    def test_unarchive_with_unauthorized_user(self):
        self._get(status=302, user=UserFactory.create())
        assert ("You don't have permission to unarchive this resource."
                in [str(m) for m in get_messages(self.request)])

        self.resource.refresh_from_db()
        assert self.resource.archived is True

    def test_unarchive_with_unauthenticated_user(self):
        response = self._get(status=302, user=AnonymousUser())
        assert '/account/login/' in response['location']

        self.resource.refresh_from_db()
        assert self.resource.archived is True
