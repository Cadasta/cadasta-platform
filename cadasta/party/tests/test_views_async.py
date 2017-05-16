import json
from django.test import TestCase
from django.template.loader import render_to_string
from skivvy import APITestCase, remove_csrf
from tutelary.models import Policy, assign_user_policies
from core.tests.utils.cases import UserTestCase
from accounts.tests.factories import UserFactory
from organization.tests.factories import ProjectFactory
from questionnaires.tests import factories as q_factories

from .factories import PartyFactory
from ..views.async import PartyList


def assign_policies(user):
    clauses = {
        'clause': [
            {
                "effect": "allow",
                "object": ["*"],
                "action": ["org.*"]
            }, {
                'effect': 'allow',
                'object': ['organization/*'],
                'action': ['org.*', "org.*.*"]
            }, {
                'effect': 'allow',
                'object': ['project/*/*'],
                'action': ['project.*', 'project.*.*', 'party.*']
            }, {
                'effect': 'allow',
                'object': ['party/*/*/*'],
                'action': ['party.*', 'party.resources.*']
            }
        ]
    }
    policy = Policy.objects.create(
        name='test-policy',
        body=json.dumps(clauses))
    assign_user_policies(user, policy)


class PartyListTest(APITestCase, UserTestCase, TestCase):
    view_class = PartyList
    get_data = {'draw': '1', 'start': 0, 'length': 10}

    def setup_models(self):
        self.user = UserFactory.create()
        self.project = ProjectFactory.create()
        PartyFactory.create_batch(100, project=self.project)
        PartyFactory.create(name='A', type='GR', project=self.project)
        PartyFactory.create(name='B', type='GR', project=self.project)
        PartyFactory.create(name='C', type='GR', project=self.project)

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def render_html_snippet(self, parties):
        html = render_to_string(
            'party/table_snippets/party.html',
            context={'parties': parties,
                     'project': self.project})

        return remove_csrf(html)

    def test_get_default(self):
        assign_policies(self.user)
        response = self.request(user=self.user)
        parties = self.project.parties.order_by('name')[0:10]

        assert response.status_code == 200
        assert response.content['draw'] == 1
        assert response.content['recordsTotal'] == 103
        assert response.content['recordsFiltered'] == 103
        assert response.content['data'] == []
        assert (remove_csrf(response.content['tbody']) ==
                self.render_html_snippet(parties))

    def test_get_private_project(self):
        self.project.access = 'private'
        self.project.save()

        assign_policies(self.user)
        response = self.request(user=self.user)
        parties = self.project.parties.order_by('name')[0:10]

        assert response.status_code == 200
        assert response.content['draw'] == 1
        assert response.content['recordsTotal'] == 103
        assert response.content['recordsFiltered'] == 103
        assert response.content['data'] == []
        assert (remove_csrf(response.content['tbody']) ==
                self.render_html_snippet(parties))

    def test_get_archived_project(self):
        self.project.archived = True
        self.project.save()

        assign_policies(self.user)
        response = self.request(user=self.user)
        parties = self.project.parties.order_by('name')[0:10]

        assert response.status_code == 200
        assert response.content['draw'] == 1
        assert response.content['recordsTotal'] == 103
        assert response.content['recordsFiltered'] == 103
        assert response.content['data'] == []
        assert (remove_csrf(response.content['tbody']) ==
                self.render_html_snippet(parties))

    def test_get_organization_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'organization': 'some-org'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_get_project_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'project': 'some-prj'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_get_with_unauthorized_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 403

    def test_get_with_unauthenticated_user(self):
        response = self.request(user=None)
        assert response.status_code == 401

    def test_get_search(self):
        assign_policies(self.user)
        response = self.request(user=self.user,
                                get_data={'search[value]': 'Party'})
        parties = self.project.parties.filter(
            name__contains='Party').order_by('name')[0:10]

        assert response.status_code == 200
        assert response.content['draw'] == 1
        assert response.content['recordsTotal'] == 103
        assert response.content['recordsFiltered'] == 100
        assert response.content['data'] == []
        assert (remove_csrf(response.content['tbody']) ==
                self.render_html_snippet(parties))

    def test_get_order_by_name_asc(self):
        assign_policies(self.user)
        response = self.request(user=self.user,
                                get_data={'order[0][column]': 0,
                                          'order[0][dir]': 'asc'})
        parties = self.project.parties.order_by('name')[0:10]

        assert response.status_code == 200
        assert response.content['draw'] == 1
        assert response.content['recordsTotal'] == 103
        assert response.content['recordsFiltered'] == 103
        assert response.content['data'] == []
        assert (remove_csrf(response.content['tbody']) ==
                self.render_html_snippet(parties))

    def test_get_order_by_name_desc(self):
        assign_policies(self.user)
        response = self.request(user=self.user,
                                get_data={'order[0][column]': 0,
                                          'order[0][dir]': 'desc'})
        parties = self.project.parties.order_by('-name')[0:10]

        assert response.status_code == 200
        assert response.content['draw'] == 1
        assert response.content['recordsTotal'] == 103
        assert response.content['recordsFiltered'] == 103
        assert response.content['data'] == []
        assert (remove_csrf(response.content['tbody']) ==
                self.render_html_snippet(parties))

    def test_get_order_by_type_asc(self):
        assign_policies(self.user)
        response = self.request(user=self.user,
                                get_data={'order[0][column]': 1,
                                          'order[0][dir]': 'asc'})
        parties = self.project.parties.order_by('type')[0:10]

        assert response.status_code == 200
        assert response.content['draw'] == 1
        assert response.content['recordsTotal'] == 103
        assert response.content['recordsFiltered'] == 103
        assert response.content['data'] == []
        assert (remove_csrf(response.content['tbody']) ==
                self.render_html_snippet(parties))

    def test_get_order_by_type_desc(self):
        assign_policies(self.user)
        response = self.request(user=self.user,
                                get_data={'order[0][column]': 1,
                                          'order[0][dir]': 'desc'})
        parties = self.project.parties.order_by('-type')[0:10]

        assert response.status_code == 200
        assert response.content['draw'] == 1
        assert response.content['recordsTotal'] == 103
        assert response.content['recordsFiltered'] == 103
        assert response.content['data'] == []
        assert (remove_csrf(response.content['tbody']) ==
                self.render_html_snippet(parties))

    def test_get_with_length(self):
        assign_policies(self.user)
        response = self.request(user=self.user,
                                get_data={'length': 25})
        parties = self.project.parties.order_by('name')[0:25]

        assert response.status_code == 200
        assert response.content['draw'] == 1
        assert response.content['recordsTotal'] == 103
        assert response.content['recordsFiltered'] == 103
        assert response.content['data'] == []
        assert (remove_csrf(response.content['tbody']) ==
                self.render_html_snippet(parties))

    def test_get_with_length_and_start(self):
        assign_policies(self.user)
        response = self.request(user=self.user,
                                get_data={'length': 15, 'start': 15})
        parties = self.project.parties.order_by('name')[15:30]

        assert response.status_code == 200
        assert response.content['draw'] == 1
        assert response.content['recordsTotal'] == 103
        assert response.content['recordsFiltered'] == 103
        assert response.content['data'] == []
        assert (remove_csrf(response.content['tbody']) ==
                self.render_html_snippet(parties))

    def test_get_with_questionnaire(self):
        questionnaire = q_factories.QuestionnaireFactory.create(
            project=self.project)

        party_type_question = q_factories.QuestionFactory.create(
            questionnaire=questionnaire,
            name='party_type',
            type='S1')
        q_factories.QuestionOptionFactory.create(
            question=party_type_question,
            name='IN',
            label={'en': 'Individual', 'de': 'Einzelperson'})
        q_factories.QuestionOptionFactory.create(
            question=party_type_question,
            name='GR',
            label={'en': 'Group', 'de': 'Gruppe'})

        assign_policies(self.user)
        response = self.request(user=self.user)
        parties = self.project.parties.order_by('name')[0:10]
        for p in parties:
            if p.type == 'GR':
                p.type_labels = ('data-label-de="Gruppe" '
                                 'data-label-en="Group"')
            elif p.type == 'IN':
                p.type_labels = ('data-label-de="Einzelperson" '
                                 'data-label-en="Individual"')

        assert response.status_code == 200
        assert response.content['draw'] == 1
        assert response.content['recordsTotal'] == 103
        assert response.content['recordsFiltered'] == 103
        assert response.content['data'] == []
        assert (remove_csrf(response.content['tbody']) ==
                self.render_html_snippet(parties))

    def test_get_with_questionnaire_no_question(self):
        q_factories.QuestionnaireFactory.create(project=self.project)

        assign_policies(self.user)
        response = self.request(user=self.user)
        parties = self.project.parties.order_by('name')[0:10]

        assert response.status_code == 200
        assert response.content['draw'] == 1
        assert response.content['recordsTotal'] == 103
        assert response.content['recordsFiltered'] == 103
        assert response.content['data'] == []
        assert (remove_csrf(response.content['tbody']) ==
                self.render_html_snippet(parties))
