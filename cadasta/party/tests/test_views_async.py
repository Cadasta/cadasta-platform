import json

import pytest

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import FileStorageTestCase, UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import TestCase
from jsonattrs.models import Attribute, AttributeType, Schema
from organization.tests.factories import ProjectFactory
from questionnaires.tests import factories as q_factories
from resources.forms import AddResourceFromLibraryForm, ResourceForm
from resources.tests.factories import ResourceFactory
from resources.tests.utils import clear_temp  # noqa
from skivvy import ViewTestCase
from spatial.models import SpatialUnit
from tutelary.models import Policy, assign_user_policies

from .. import forms
from ..models import Party, TenureRelationship, TenureRelationshipType
from ..views import async
from .factories import TenureRelationshipFactory


def assign_policies(user):
    clauses = {
        'clause': [
            {
                'effect': 'allow',
                'object': ['project/*/*'],
                'action': ['project.*.*', 'party.*', 'tenure_rel.*']
            },
            {
                'effect': 'allow',
                'object': ['party/*/*/*'],
                'action': ['party.*', 'party.*.*']
            },
            {
                'effect': 'allow',
                'object': ['tenure_rel/*/*/*'],
                'action': ['tenure_rel.*', 'tenure_rel.*.*']
            }
        ]
    }
    policy = Policy.objects.create(
        name='allow',
        body=json.dumps(clauses))
    assign_user_policies(user, policy)


class PartyRelationshipDetailTest(ViewTestCase, UserTestCase, TestCase):
    view_class = async.PartyRelationshipDetail
    template = 'party/relationship_detail.html'

    def setup_models(self):
        self.project = ProjectFactory.create()
        content_type = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(self.project.organization.id, self.project.id, ))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='fname', long_name='Test field',
            attr_type=attr_type, index=0,
            required=False, omit=False
        )
        Attribute.objects.create(
            schema=schema,
            name='fname_2', long_name='Test field 2',
            attr_type=AttributeType.objects.get(name='select_one'),
            choices=['-', 'one', 'two', 'three'],
            choice_labels=['None', 'Choice 1', 'Choice 2', 'Choice 3'],
            index=1,
            required=False, omit=False
        )
        Attribute.objects.create(
            schema=schema,
            name='fname_3', long_name='Test field 3',
            attr_type=AttributeType.objects.get(name='select_multiple'),
            choices=['-', 'one', 'two', 'three'],
            choice_labels=['None', 'Choice 1', 'Choice 2', 'Choice 3'],
            index=2,
            required=False, omit=False
        )
        self.relationship = TenureRelationshipFactory.create(
            project=self.project, attributes={
                'fname': 'test',
                'fname_2': 'two',
                'fname_3': ['one', 'three']
            },
            spatial_unit__geometry='SRID=4326;POINT(11 53)')

    def setup_template_context(self):
        return {'object': self.project,
                'relationship': self.relationship,
                'location': self.relationship.spatial_unit,
                'attributes': (('Test field', 'test', ),
                               ('Test field 2', 'Choice 2', ),
                               ('Test field 3', 'Choice 1, Choice 3', ))}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'relationship': self.relationship.id
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content
        assert 'coordinates' in response.headers

    def test_get_with_incomplete_questionnaire(self):
        questionnaire = q_factories.QuestionnaireFactory.create()
        self.project.current_questionnaire = questionnaire.id
        self.project.save()

        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_questionnaire(self):
        questionnaire = q_factories.QuestionnaireFactory.create()
        self.project.current_questionnaire = questionnaire.id
        self.project.save()

        tenure_type_question = q_factories.QuestionFactory.create(
            questionnaire=questionnaire,
            name='tenure_type',
            label={'en': 'Tenure type', 'de': 'Anrecht'},
            type='S1')
        q_factories.QuestionOptionFactory.create(
            question=tenure_type_question,
            name=self.relationship.tenure_type_id,
            label={'en': 'Some type', 'de': 'Ein Typ'})

        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.render_content(
            type_labels=('data-label-de="Anrecht" '
                         'data-label-en="Tenure type"'),
            type_choice_labels=('data-label-de="Ein Typ" '
                                'data-label-en="Some type"'),
            form_lang_default='en',
            form_langs=[('en', 'English'), ('de', 'German')])

    def test_get_with_questionnaire_but_missing_option(self):
        questionnaire = q_factories.QuestionnaireFactory.create()
        self.project.current_questionnaire = questionnaire.id
        self.project.save()

        q_factories.QuestionFactory.create(
            questionnaire=questionnaire,
            name='tenure_type',
            label={'en': 'Tenure type', 'de': 'Anrecht'},
            type='S1')

        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.render_content(
            type_labels=('data-label-de="Anrecht" '
                         'data-label-en="Tenure type"'),
            form_lang_default='en',
            form_langs=[('en', 'English'), ('de', 'German')])

    def test_get_from_non_existent_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existent_relationship(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'relationship': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to view this tenure relationship."
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location


class PartyRelationshipEditTest(ViewTestCase, UserTestCase, TestCase):
    view_class = async.PartyRelationshipEdit
    template = 'party/relationship_edit.html'
    post_data = {
        'tenure_type': 'LH',
        'tenurerelationship::default::fname': 'New text'
    }

    def setup_models(self):
        self.project = ProjectFactory.create()
        content_type = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(self.project.organization.id, self.project.id, ))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='fname', long_name='Test field',
            attr_type=attr_type, index=0,
            required=False, omit=False
        )
        self.relationship = TenureRelationshipFactory.create(
            project=self.project,
            attributes={'fname': 'test'},
            tenure_type=TenureRelationshipType.objects.get(id='WR'),
            spatial_unit__geometry=('SRID=4326;POINT(11 53)')
        )

    def setup_template_context(self):
        form = forms.TenureRelationshipEditForm(instance=self.relationship)
        submit_url = reverse('async:party:delete', kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug,
                'relationship': self.relationship.id
            })
        return {'object': self.project,
                'relationship': self.relationship,
                'location': self.relationship.spatial_unit,
                'form': form,
                'cancel_url': '#/records/relationship/{}/'.format(
                                self.relationship.id),
                'submit_url': submit_url}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'relationship': self.relationship.id
        }

    def get_success_url(self):
        url_kwargs = self.setup_url_kwargs()
        return (reverse('organization:project-dashboard', kwargs={
                'organization': url_kwargs['organization'],
                'project': url_kwargs['project'],
                }) +
                '#/records/relationship/{}/'.format(
                    url_kwargs['relationship']))

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert ('<input class="form-control" '
                'id="id_tenurerelationship::default::fname" '
                'name="tenurerelationship::default::fname" '
                'type="text" value="test" />') in response.content
        assert 'coordinates' in response.headers

    def test_get_from_non_existent_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existent_relationship(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'relationship': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to update this tenure relationship."
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_get_with_archived_project(self):
        self.project.archived = True
        self.project.save()

        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to update this tenure relationship."
                in response.messages)

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url

        # attributes field is deferred so we fetch a fresh instance
        relationship = TenureRelationship.objects.defer(None).get(
            id=self.relationship.id)
        assert relationship.tenure_type_id == 'LH'
        assert relationship.attributes.get('fname') == 'New text'

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to update this tenure relationship."
                in response.messages)

        self.relationship.refresh_from_db()
        assert self.relationship.tenure_type_id != 'LH'

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location

        self.relationship.refresh_from_db()
        assert self.relationship.tenure_type_id != 'LH'

    def test_post_with_archived_project(self):
        self.project.archived = True
        self.project.save()

        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to update this tenure relationship."
                in response.messages)

        self.relationship.refresh_from_db()
        assert self.relationship.tenure_type_id != 'LH'

    def test_post_with_bad_data(self):
        user = UserFactory.create()
        assign_policies(user)

        response = self.request(method='POST', user=user, post_data={
            'tenure_type': 'Bad request'
            })
        assert response.status_code == 200
        assert 'form-error' in response.headers

        # attributes field is deferred so we fetch a fresh instance
        relationship = TenureRelationship.objects.defer(None).get(
            id=self.relationship.id)
        assert relationship.tenure_type_id == 'WR'
        assert relationship.attributes.get('fname') == 'test'


class PartyRelationshipDeleteTest(ViewTestCase, UserTestCase, TestCase):
    view_class = async.PartyRelationshipDelete
    template = 'party/relationship_delete.html'
    post_data = {}

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.relationship = TenureRelationshipFactory.create(
            project=self.project,
            spatial_unit__geometry='SRID=4326;POINT(11 53)')

    def setup_template_context(self):
        submit_url = reverse('async:party:relationship_delete', kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug,
                'relationship': self.relationship.id
            })
        return {'object': self.project,
                'relationship': self.relationship,
                'location': self.relationship.spatial_unit,
                'cancel_url': '#/records/relationship/{}/'.format(
                                self.relationship.id),
                'submit_url': submit_url}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'relationship': self.relationship.id
        }

    def get_success_url(self):
        url_kwargs = self.setup_url_kwargs()
        return (reverse('organization:project-dashboard', kwargs={
                'organization': url_kwargs['organization'],
                'project': url_kwargs['project'],
                }))

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content
        assert 'coordinates' in response.headers

    def test_get_from_non_existent_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existent_relationship(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'relationship': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to remove this tenure relationship."
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_get_with_archived_project(self):
        self.project.archived = True
        self.project.save()

        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to remove this tenure relationship."
                in response.messages)

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url

        assert TenureRelationship.objects.count() == 0
        assert SpatialUnit.objects.count() == 1
        assert Party.objects.count() == 1

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to remove this tenure relationship."
                in response.messages)

        assert TenureRelationship.objects.count() == 1

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location
        self.relationship.refresh_from_db()
        assert TenureRelationship.objects.count() == 1

    def test_post_with_archived_project(self):
        self.project.archived = True
        self.project.save()

        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to remove this tenure relationship."
                in response.messages)

        assert TenureRelationship.objects.count() == 1


@pytest.mark.usefixtures('make_dirs')
class PartyRelationshipResourceAddTest(ViewTestCase, UserTestCase, TestCase):
    view_class = async.PartyRelationshipResourceAdd
    template = 'party/relationship_resources_add.html'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.relationship = TenureRelationshipFactory.create(
            project=self.project,
            spatial_unit__geometry='SRID=4326;POINT(11 53)')
        self.attached = ResourceFactory.create(
            project=self.project, content_object=self.relationship)
        self.unattached = ResourceFactory.create(project=self.project)

    def setup_template_context(self):
        form = AddResourceFromLibraryForm(content_object=self.relationship,
                                          project_id=self.project.id)
        submit_url = reverse('async:party:relationship_resource_add', kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug,
                'relationship': self.relationship.id
            })
        return {'object': self.project,
                'relationship': self.relationship,
                'location': self.relationship.spatial_unit,
                'form': form,
                'cancel_url': '#/records/relationship/{}/'.format(
                                self.relationship.id),
                'submit_url': submit_url,
                'upload_url': ("#/records/relationship/{}"
                               "/resources/new/".format(
                                  self.relationship.id))
                }

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'relationship': self.relationship.id
        }

    def get_success_url(self):
        url_kwargs = self.setup_url_kwargs()
        return (reverse('organization:project-dashboard', kwargs={
                'organization': url_kwargs['organization'],
                'project': url_kwargs['project'],
                }) +
                '#/records/relationship/{}/'.format(
                    url_kwargs['relationship']))

    def setup_post_data(self):
        return {
            self.attached.id: False,
            self.unattached.id: True,
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content
        assert 'coordinates' in response.headers

    def test_get_from_non_existent_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existent_relationship(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'relationship': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add resources to this tenure "
                "relationship."
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_get_with_archived_project(self):
        self.project.archived = True
        self.project.save()

        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add resources to this tenure "
                "relationship."
                in response.messages)

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url

        relationship_resources = self.relationship.resources.all()
        assert len(relationship_resources) == 2
        assert self.attached in relationship_resources
        assert self.unattached in relationship_resources

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add resources to this tenure "
                "relationship."
                in response.messages)

        assert self.relationship.resources.count() == 1
        assert self.relationship.resources.first() == self.attached

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location

        assert self.relationship.resources.count() == 1
        assert self.relationship.resources.first() == self.attached

    def test_post_with_archived_project(self):
        self.project.archived = True
        self.project.save()

        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add resources to this tenure "
                "relationship."
                in response.messages)

        assert self.relationship.resources.count() == 1
        assert self.relationship.resources.first() == self.attached


@pytest.mark.usefixtures('make_dirs')
class PartyRelationshipResourceNewTest(ViewTestCase, UserTestCase,
                                       FileStorageTestCase, TestCase):
    view_class = async.PartyRelationshipResourceNew
    template = 'party/relationship_resources_new.html'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.relationship = TenureRelationshipFactory.create(
            project=self.project,
            spatial_unit__geometry='SRID=4326;POINT(11 53)')

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'relationship': self.relationship.id
        }

    def get_success_url(self):
        url_kwargs = self.setup_url_kwargs()
        return (reverse('organization:project-dashboard', kwargs={
                'organization': url_kwargs['organization'],
                'project': url_kwargs['project'],
                }) +
                '#/records/relationship/{}/'.format(
                    url_kwargs['relationship']))

    def setup_template_context(self):
        form = ResourceForm(content_object=self.relationship,
                            project_id=self.project.id)
        submit_url = reverse('async:party:relationship_resource_new', kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug,
                'relationship': self.relationship.id
            })
        return {'object': self.project,
                'location': self.relationship.spatial_unit,
                'relationship': self.relationship,
                'form': form,
                'cancel_url': '#/records/relationship/{}/'.format(
                                self.relationship.id),
                'submit_url': submit_url}

    def setup_post_data(self):
        file = self.get_file('/resources/tests/files/image.jpg', 'rb')
        file_name = self.storage.save('resources/image.jpg', file)

        return {
            'name': 'Some name',
            'description': '',
            'file': file_name,
            'original_file': 'image.png',
            'mime_type': 'image/jpeg'
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content
        assert 'coordinates' in response.headers

    def test_get_from_non_existent_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existent_relationship(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'relationship': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add resources to this tenure "
                "relationship."
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_get_with_archived_project(self):
        self.project.archived = True
        self.project.save()

        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add resources to this tenure "
                "relationship."
                in response.messages)

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url

        assert self.relationship.resources.count() == 1

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add resources to this tenure "
                "relationship."
                in response.messages)

        assert self.relationship.resources.count() == 0

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location

        assert self.relationship.resources.count() == 0

    def test_post_with_archived_project(self):
        self.project.archived = True
        self.project.save()

        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add resources to this tenure "
                "relationship."
                in response.messages)

    def test_post_with_bad_data(self):
        post_data = {
            'name': '',
            'description': '',
            'original_file': 'image.png',
            'mime_type': 'image/jpeg'
        }

        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user, post_data=post_data)
        assert response.status_code == 200
        assert 'form-error' in response.headers
