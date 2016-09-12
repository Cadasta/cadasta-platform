import json
import os
import pytest
from django.http import Http404
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from buckets.test.storage import FakeS3Storage
from tutelary.models import Policy, assign_user_policies
from jsonattrs.models import Attribute, AttributeType, Schema
from skivvy import ViewTestCase

from accounts.tests.factories import UserFactory
from organization.tests.factories import ProjectFactory
from resources.tests.factories import ResourceFactory
from resources.tests.utils import clear_temp  # noqa
from resources.forms import AddResourceFromLibraryForm, ResourceForm
from core.tests.utils.cases import UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from spatial.models import SpatialUnit

from ..models import Party, TenureRelationship, TenureRelationshipType
from .. import forms
from ..views import default
from .factories import PartyFactory, TenureRelationshipFactory


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


class PartiesListTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PartiesList
    template = 'party/party_list.html'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.parties = PartyFactory.create_batch(
            2, project=self.project)
        PartyFactory.create()

    def setup_template_context(self):
        return {'object': self.project, 'object_list': self.parties}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_from_non_existend_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.render_content(object_list=[])

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location


class PartiesAddTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PartiesAdd
    template = 'party/party_add.html'
    success_url_name = 'parties:detail'
    post_data = {
        'name': 'Party',
        'type': 'GR'
    }

    def setup_models(self):
        self.project = ProjectFactory.create()

    def setup_template_context(self):
        return {
            'object': self.project,
            'form': forms.PartyForm(schema_selectors=())
        }

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def setup_success_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'party': self.party_created.id
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_from_non_existend_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add parties to this project."
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert Party.objects.count() == 1
        self.party_created = Party.objects.first()
        assert response.status_code == 302
        assert response.location == self.expected_success_url

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert Party.objects.count() == 0
        assert response.status_code == 302
        assert ("You don't have permission to add parties to this project."
                in response.messages)

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert Party.objects.count() == 0
        assert response.status_code == 302
        assert '/account/login/' in response.location


class PartyDetailTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PartiesDetail
    template = 'party/party_detail.html'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.party = PartyFactory.create(project=self.project)
        content_type = ContentType.objects.get(
            app_label='party', model='party')
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
        self.party = PartyFactory.create(project=self.project,
                                         attributes={'fname': 'test'})

    def setup_template_context(self):
        return {'object': self.project,
                'party': self.party,
                'attributes': (('Test field', 'test', ), )}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'party': self.party.id
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_from_non_existend_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existend_party(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'party': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to view this party."
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location


class PartiesEditTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PartiesEdit
    template = 'party/party_edit.html'
    success_url_name = 'parties:detail'
    post_data = {
        'name': 'Party',
        'type': 'GR',
        'attributes::fname': 'New text'
    }

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.party = PartyFactory.create(project=self.project)
        content_type = ContentType.objects.get(
            app_label='party', model='party')
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
        self.party = PartyFactory.create(project=self.project,
                                         attributes={'fname': 'test'})

    def setup_template_context(self):
        return {'object': self.project,
                'party': self.party,
                'form': forms.PartyForm(instance=self.party)}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'party': self.party.id
        }

    def setup_success_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'party': self.party.id
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to update this party."
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_get_from_non_existend_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existend_party(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'party': 'abc123'})

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url

        self.party.refresh_from_db()
        assert self.party.name == self.post_data['name']
        assert self.party.type == self.post_data['type']
        assert self.party.attributes.get('fname') == 'New text'

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to update this party."
                in response.messages)

        self.party.refresh_from_db()
        assert self.party.name != self.post_data['name']
        assert self.party.type != self.post_data['type']

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location

        self.party.refresh_from_db()
        assert self.party.name != self.post_data['name']
        assert self.party.type != self.post_data['type']


class PartiesDeleteTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PartiesDelete
    template = 'party/party_delete.html'
    success_url_name = 'locations:list'
    post_data = {}

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.party = PartyFactory.create(project=self.project)
        TenureRelationshipFactory.create(
            project=self.project, party=self.party)

    def setup_template_context(self):
        return {'object': self.project, 'party': self.party}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'party': self.party.id
        }

    def setup_success_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to remove this party."
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_get_from_non_existend_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existend_party(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'party': 'abc123'})

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url

        assert Party.objects.count() == 0
        assert TenureRelationship.objects.count() == 0

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to remove this party."
                in response.messages)

        assert Party.objects.count() == 1
        assert TenureRelationship.objects.count() == 1

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location

        assert Party.objects.count() == 1
        assert TenureRelationship.objects.count() == 1


@pytest.mark.usefixtures('make_dirs')
class PartyResourcesAddTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PartyResourcesAdd
    template = 'party/resources_add.html'
    success_url_name = 'parties:detail'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.party = PartyFactory.create(project=self.project)
        self.attached = ResourceFactory.create(project=self.project,
                                               content_object=self.party)
        self.unattached = ResourceFactory.create(project=self.project)

    def setup_template_context(self):
        form = AddResourceFromLibraryForm(content_object=self.party,
                                          project_id=self.project.id)
        return {'object': self.project,
                'party': self.party,
                'form': form}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'party': self.party.id
        }

    def setup_success_url_kwargs(self):
        return self.setup_url_kwargs()

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

    def test_get_from_non_existend_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existend_party(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'party': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add resources to this party"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url

        party_resources = self.party.resources.all()
        assert len(party_resources) == 2
        assert self.attached in party_resources
        assert self.unattached in party_resources

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add resources to this party"
                in response.messages)

        assert self.party.resources.count() == 1
        assert self.party.resources.first() == self.attached

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location

        assert self.party.resources.count() == 1
        assert self.party.resources.first() == self.attached


@pytest.mark.usefixtures('make_dirs')
@pytest.mark.usefixtures('clear_temp')
class PartyResourcesNewTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PartyResourcesNew
    template = 'party/resources_new.html'
    success_url_name = 'parties:detail'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.party = PartyFactory.create(project=self.project)

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'party': self.party.id
        }

    def setup_success_url_kwargs(self):
        return self.setup_url_kwargs()

    def setup_template_context(self):
        form = ResourceForm(content_object=self.party,
                            project_id=self.project.id)
        return {'object': self.project,
                'party': self.party,
                'form': form}

    def setup_post_data(self):
        path = os.path.dirname(settings.BASE_DIR)
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

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_from_non_existend_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existend_party(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'party': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add resources to this party"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url

        assert self.party.resources.count() == 1

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add resources to this party"
                in response.messages)

        assert self.party.resources.count() == 0

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location

        assert self.party.resources.count() == 0


class PartyRelationshipDetailTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PartyRelationshipDetail
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
        self.relationship = TenureRelationshipFactory.create(
            project=self.project, attributes={'fname': 'test'})

    def setup_template_context(self):
        return {'object': self.project,
                'relationship': self.relationship,
                'location': self.relationship.spatial_unit,
                'geojson': '{"type": "FeatureCollection", "features": []}',
                'attributes': (('Test field', 'test', ), )}

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

    def test_get_from_non_existend_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existend_relationship(self):
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
    view_class = default.PartyRelationshipEdit
    template = 'party/relationship_edit.html'
    success_url_name = 'parties:relationship_detail'
    post_data = {'tenure_type': 'LH', 'attributes::fname': 'New text'}

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
            tenure_type=TenureRelationshipType.objects.get(id='WR')
        )

    def setup_template_context(self):
        form = forms.TenureRelationshipEditForm(instance=self.relationship)
        return {'object': self.project,
                'relationship': self.relationship,
                'location': self.relationship.spatial_unit,
                'form': form,
                'geojson': '{"type": "FeatureCollection", "features": []}'}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'relationship': self.relationship.id
        }

    def setup_success_url_kwargs(self):
        return self.setup_url_kwargs()

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_from_non_existend_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existend_relationship(self):
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

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url

        self.relationship.refresh_from_db()
        assert self.relationship.tenure_type_id == 'LH'
        assert self.relationship.attributes.get('fname') == 'New text'

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

        print(self.relationship.tenure_type_id)
        self.relationship.refresh_from_db()
        assert self.relationship.tenure_type_id != 'LH'


class PartyRelationshipDeleteTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PartyRelationshipDelete
    template = 'party/relationship_delete.html'
    success_url_name = 'locations:list'
    post_data = {}

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.relationship = TenureRelationshipFactory.create(
            project=self.project)

    def setup_template_context(self):
        return {'object': self.project,
                'relationship': self.relationship,
                'location': self.relationship.spatial_unit,
                'geojson': '{"type": "FeatureCollection", "features": []}'}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'relationship': self.relationship.id
        }

    def setup_success_url_kwargs(self):
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

    def test_get_from_non_existend_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existend_relationship(self):
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


@pytest.mark.usefixtures('make_dirs')
class PartyRelationshipResourceAddTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PartyRelationshipResourceAdd
    template = 'party/relationship_resources_add.html'
    success_url_name = 'parties:relationship_detail'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.relationship = TenureRelationshipFactory.create(
            project=self.project)
        self.attached = ResourceFactory.create(
            project=self.project, content_object=self.relationship)
        self.unattached = ResourceFactory.create(project=self.project)

    def setup_template_context(self):
        form = AddResourceFromLibraryForm(content_object=self.relationship,
                                          project_id=self.project.id)
        return {'object': self.project,
                'relationship': self.relationship,
                'location': self.relationship.spatial_unit,
                'form': form,
                'geojson': '{"type": "FeatureCollection", "features": []}'}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'relationship': self.relationship.id
        }

    def setup_success_url_kwargs(self):
        return self.setup_url_kwargs()

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

    def test_get_from_non_existend_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existend_relationship(self):
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


@pytest.mark.usefixtures('make_dirs')
class PartyRelationshipResourceNewTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PartyRelationshipResourceNew
    template = 'party/relationship_resources_new.html'
    success_url_name = 'parties:relationship_detail'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.relationship = TenureRelationshipFactory.create(
            project=self.project)

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'relationship': self.relationship.id
        }

    def setup_template_context(self):
        form = ResourceForm(content_object=self.relationship,
                            project_id=self.project.id)
        return {'object': self.project,
                'location': self.relationship.spatial_unit,
                'relationship': self.relationship,
                'form': form,
                'geojson': '{"type": "FeatureCollection", "features": []}'}

    def setup_post_data(self):
        path = os.path.dirname(settings.BASE_DIR)
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

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_from_non_existend_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existend_relationship(self):
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
