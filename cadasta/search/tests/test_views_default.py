import pytest
import json
from django.http import Http404
from django.test import TestCase

from tutelary.models import Policy, assign_user_policies
from skivvy import ViewTestCase

from accounts.tests.factories import UserFactory
from organization.tests.factories import ProjectFactory
from core.tests.utils.cases import UserTestCase

from ..views import default


def assign_policies(user):
    clauses = {
        'clause': [
            {
                'effect': 'allow',
                'object': ['project/*/*'],
                'action': ['project.view_private']
            },
        ],
    }
    policy = Policy.objects.create(
        name='allow',
        body=json.dumps(clauses))
    assign_user_policies(user, policy)


class SearchTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.Search
    template = 'search/search.html'

    def setup_models(self):
        self.project = ProjectFactory.create()

    def setup_template_context(self):
        return {
            'object': self.project,
        }

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_from_non_existent_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to access this project"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location
