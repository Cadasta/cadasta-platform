import os
import pytest
import json
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
from core.tests.utils.cases import UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from resources.tests.factories import ResourceFactory
from resources.tests.utils import clear_temp  # noqa
from resources.forms import AddResourceFromLibraryForm, ResourceForm
from party.tests.factories import PartyFactory, TenureRelationshipFactory
from party.models import Party, TenureRelationship

from .factories import SpatialUnitFactory
from ..views import default
from .. import forms
from ..models import SpatialUnit
from ..serializers import SpatialUnitGeoJsonSerializer


def assign_policies(user):
    clauses = {
        'clause': [
            {
                'effect': 'allow',
                'object': ['project/*/*'],
                'action': ['spatial.*', 'tenure_rel.*']
            },
            {
                'effect': 'allow',
                'object': ['spatial/*/*/*'],
                'action': ['spatial.*', 'spatial.*.*']
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


class LocationsListTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.LocationsList
    template = 'spatial/location_map.html'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.locations = SpatialUnitFactory.create_batch(
            2, project=self.project)
        SpatialUnitFactory.create()

    def setup_template_context(self):
        geojson = json.dumps(
            SpatialUnitGeoJsonSerializer(self.locations, many=True).data)
        return {
            'object': self.project,
            'object_list': self.locations,
            'geojson': geojson
        }

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
        assert response.content == self.expected_content

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location


class LocationAddTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.LocationsAdd
    template = 'spatial/location_add.html'
    success_url_name = 'locations:detail'
    post_data = {
        'geometry': '{"type": "Polygon","coordinates": [[[-0.1418137550354'
                    '004,51.55240622205599],[-0.14117002487182617,51.55167'
                    '905819532],[-0.1411914825439453,51.55181915488898],[-'
                    '0.1411271095275879,51.55254631651022],[-0.14181375503'
                    '54004,51.55240622205599]]]}',
        'type': 'CB',
        'attributes::fname': 'Test text'
    }

    def setup_models(self):
        self.project = ProjectFactory.create(current_questionnaire='a1')
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialunit')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(self.project.organization.id, self.project.id, 'a1'))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='fname', long_name='Test field',
            attr_type=attr_type, index=0,
            required=False, omit=False
        )

    def setup_template_context(self):
        return {
            'object': self.project,
            'form': forms.LocationForm(
                schema_selectors=(
                    {'name': 'organization',
                     'value': self.project.organization,
                     'selector': self.project.organization.id},
                    {'name': 'project',
                     'value': self.project,
                     'selector': self.project.id},
                    {'name': 'questionnaire',
                     'value': self.project.current_questionnaire,
                     'selector': self.project.current_questionnaire}
                )
            ),
            'geojson': '{"type": "FeatureCollection", "features": []}'
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
            'location': self.location_created.id
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
        assert ("You don't have permission to add "
                "locations to this project." in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)

        assert SpatialUnit.objects.count() == 1
        self.location_created = SpatialUnit.objects.first()
        assert self.location_created.attributes.get('fname') == 'Test text'
        assert response.status_code == 302
        assert response.location == self.expected_success_url

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert SpatialUnit.objects.count() == 0
        assert response.status_code == 302
        assert ("You don't have permission to add "
                "locations to this project." in response.messages)

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert SpatialUnit.objects.count() == 0
        assert response.status_code == 302
        assert '/account/login/' in response.location


class LocationDetailTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.LocationDetail
    template = 'spatial/location_detail.html'

    def setup_models(self):
        self.project = ProjectFactory.create()
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialunit')
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
        self.location = SpatialUnitFactory.create(
            project=self.project, attributes={'fname': 'test'})

    def setup_template_context(self):
        return {
            'object': self.project,
            'location': self.location,
            'geojson': '{"type": "FeatureCollection", "features": []}',
            'attributes': (('Test field', 'test', ), )
        }

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'location': self.location.id
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

    def test_get_non_existend_location(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'location': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to view this location."
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location


class LocationEditTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.LocationEdit
    template = 'spatial/location_edit.html'
    success_url_name = 'locations:detail'
    post_data = {
        'geometry': '{"type": "Polygon","coordinates": [[[-0.1418137550354'
                    '004,51.55240622205599],[-0.14117002487182617,51.55167'
                    '905819532],[-0.1411914825439453,51.55181915488898],[-'
                    '0.1411271095275879,51.55254631651022],[-0.14181375503'
                    '54004,51.55240622205599]]]}',
        'type': 'NP',
        'attributes::fname': 'New text'
    }

    def setup_models(self):
        self.project = ProjectFactory.create()
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialunit')
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
        self.location = SpatialUnitFactory.create(
            project=self.project, attributes={'fname': 'test'})

    def setup_template_context(self):
        return {'object': self.project,
                'location': self.location,
                'form': forms.LocationForm(instance=self.location),
                'geojson': '{"type": "FeatureCollection", "features": []}'}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'location': self.location.id
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

    def test_get_non_existend_location(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'location': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to update this location."
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

        self.location.refresh_from_db()
        assert self.location.type == self.post_data['type']
        assert self.location.attributes.get('fname') == 'New text'

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to update this location."
                in response.messages)
        self.location.refresh_from_db()
        assert self.location.type != self.post_data['type']

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location
        self.location.refresh_from_db()
        assert self.location.type != self.post_data['type']


class LocationDelete(ViewTestCase, UserTestCase, TestCase):
    view_class = default.LocationDelete
    template = 'spatial/location_delete.html'
    success_url_name = 'locations:list'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.location = SpatialUnitFactory.create(project=self.project)
        TenureRelationshipFactory.create(
            project=self.project, spatial_unit=self.location)

    def setup_template_context(self):
        return {'object': self.project,
                'location': self.location,
                'geojson': '{"type": "FeatureCollection", "features": []}'}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'location': self.location.id
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

    def test_get_from_non_existend_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existend_location(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'location': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to remove this location."
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

        assert SpatialUnit.objects.count() == 0
        assert TenureRelationship.objects.count() == 0

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to remove this location."
                in response.messages)
        assert SpatialUnit.objects.count() == 1
        assert TenureRelationship.objects.count() == 1

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert SpatialUnit.objects.count() == 1
        assert TenureRelationship.objects.count() == 1


@pytest.mark.usefixtures('make_dirs')
class LocationResourceAddTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.LocationResourceAdd
    template = 'spatial/resources_add.html'
    success_url_name = 'locations:detail'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.location = SpatialUnitFactory.create(project=self.project)
        self.attached = ResourceFactory.create(project=self.project,
                                               content_object=self.location)
        self.unattached = ResourceFactory.create(project=self.project)

    def setup_template_context(self):
        form = AddResourceFromLibraryForm(content_object=self.location,
                                          project_id=self.project.id)
        return {'object': self.project,
                'location': self.location,
                'form': form,
                'geojson': '{"type": "FeatureCollection", "features": []}'}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'location': self.location.id
        }

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

    def test_get_non_existend_location(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'location': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to "
                "add resources to this location." in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url + '#resources'

        location_resources = self.location.resources.all()
        assert len(location_resources) == 2
        assert self.attached in location_resources
        assert self.unattached in location_resources

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to "
                "add resources to this location." in response.messages)
        assert self.location.resources.count() == 1
        assert self.location.resources.first() == self.attached

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert self.location.resources.count() == 1
        assert self.location.resources.first() == self.attached


@pytest.mark.usefixtures('make_dirs')
@pytest.mark.usefixtures('clear_temp')
class LocationResourceNewTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.LocationResourceNew
    template = 'spatial/resources_new.html'
    success_url_name = 'locations:detail'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.location = SpatialUnitFactory.create(project=self.project)

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'location': self.location.id
        }

    def setup_template_context(self):
        form = ResourceForm(content_object=self.location,
                            project_id=self.project.id)
        return {'object': self.project,
                'location': self.location,
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

    def test_get_non_existend_location(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'location': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to "
                "add resources to this location." in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url + '#resources'

        assert self.location.resources.count() == 1

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to "
                "add resources to this location." in response.messages)
        assert self.location.resources.count() == 0

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert self.location.resources.count() == 0


class TenureRelationshipAddTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.TenureRelationshipAdd
    template = 'spatial/relationship_add.html'
    success_url_name = 'locations:detail'
    post_data = {
        'new_entity': 'on',
        'id': '',
        'name': 'The Beatles',
        'party_type': 'GR',
        'tenure_type': 'CU',
        'party::p_name': 'Party Name',
        'relationship::r_name': 'Rel Name'
    }

    def setup_models(self):
        self.project = ProjectFactory.create(current_questionnaire='a1')
        self.spatial_unit = SpatialUnitFactory(project=self.project)
        content_type = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(self.project.organization.id, self.project.id, 'a1'))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='r_name', long_name='Relationship field',
            attr_type=attr_type, index=0,
            required=False, omit=False
        )

        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(self.project.organization.id, self.project.id, 'a1'))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='p_name', long_name='Party field',
            attr_type=attr_type, index=0,
            required=False, omit=False
        )

    def setup_template_context(self):
        return {
            'object': self.project,
            'location': self.spatial_unit,
            'form': forms.TenureRelationshipForm(
                project=self.project,
                spatial_unit=self.spatial_unit,
                schema_selectors=(
                    {'name': 'organization',
                     'value': self.project.organization,
                     'selector': self.project.organization.id},
                    {'name': 'project',
                     'value': self.project,
                     'selector': self.project.id},
                    {'name': 'questionnaire',
                     'value': self.project.current_questionnaire,
                     'selector': self.project.current_questionnaire}
                ),
                initial={
                    'new_entity': not self.project.parties.exists(),
                },
            ),
            'geojson': json.dumps(SpatialUnitGeoJsonSerializer(
                [self.spatial_unit], many=True).data),
        }
        # return {
        #     'object': self.project,
        #     'location': self.spatial_unit,
        #     'form': forms.TenureRelationshipForm(
        #         project=self.project,
        #         spatial_unit=self.spatial_unit,
        #         schema_selectors=(
        #             {'name': 'organization',
        #              'value': self.project.organization,
        #              'selector': self.project.organization.id},
        #             {'name': 'project',
        #              'value': self.project,
        #              'selector': self.project.id},
        #             {'name': 'questionnaire',
        #              'value': self.project.current_questionnaire,
        #              'selector': self.project.current_questionnaire}
        #         )),
        #     'geojson': json.dumps(SpatialUnitGeoJsonSerializer(
        #         [self.spatial_unit], many=True).data)
        # }

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'location': self.spatial_unit.id
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

    def test_get_non_existent_location(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'location': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add tenure relationships to "
                "this project." in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_post_new_party_with_authorized(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert (response.location ==
                self.expected_success_url + '#relationships')

        assert TenureRelationship.objects.count() == 1
        rel = TenureRelationship.objects.first()
        assert rel.attributes.get('r_name') == 'Rel Name'
        assert Party.objects.count() == 1
        party = Party.objects.first()
        assert party.attributes.get('p_name') == 'Party Name'

    def test_post_existing_party_with_authorized(self):
        user = UserFactory.create()
        assign_policies(user)
        party = PartyFactory.create(project=self.project)
        response = self.request(method='POST', user=user,
                                post_data={'new_entity': '', 'id': party.id})
        assert response.status_code == 302
        assert (response.location ==
                self.expected_success_url + '#relationships')

        assert TenureRelationship.objects.count() == 1
        rel = TenureRelationship.objects.first()
        assert rel.attributes.get('r_name') == 'Rel Name'
        assert Party.objects.count() == 1
        assert Party.objects.first().name == party.name

    def test_post_with_authorized_invalid_new_party_data(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST',
                                user=user,
                                post_data={'name': '', 'party_type': ''})
        assert response.status_code == 200
        data = self.post_data.copy()
        data.update({'name': '', 'party_type': ''})
        form = forms.TenureRelationshipForm(
            project=self.project,
            spatial_unit=self.spatial_unit,
            data=data,
            schema_selectors=(
                {'name': 'organization',
                 'value': self.project.organization,
                 'selector': self.project.organization.id},
                {'name': 'project',
                 'value': self.project,
                 'selector': self.project.id},
                {'name': 'questionnaire',
                 'value': self.project.current_questionnaire,
                 'selector': self.project.current_questionnaire}
            ))
        expected = self.render_content(form=form)
        assert response.content == expected

        assert TenureRelationship.objects.count() == 0
        assert Party.objects.count() == 0

    def test_post_with_authorized_invalid_existing_party_data(self):
        user = UserFactory.create()
        assign_policies(user)

        party = PartyFactory.create(project=self.project)
        response = self.request(method='POST',
                                user=user,
                                post_data={'new_entity': ''})

        data = self.post_data.copy()
        data['new_entity'] = ''
        form = forms.TenureRelationshipForm(
            project=self.project,
            spatial_unit=self.spatial_unit,
            data=data,
            schema_selectors=(
                {'name': 'organization',
                 'value': self.project.organization,
                 'selector': self.project.organization.id},
                {'name': 'project',
                 'value': self.project,
                 'selector': self.project.id},
                {'name': 'questionnaire',
                 'value': self.project.current_questionnaire,
                 'selector': self.project.current_questionnaire}
            )
        )
        assert response.status_code == 200
        assert response.content == self.render_content(form=form)
        assert TenureRelationship.objects.count() == 0
        assert Party.objects.count() == 1
        assert Party.objects.first().name == party.name

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add tenure relationships to "
                "this project."
                in response.messages)
        assert TenureRelationship.objects.count() == 0
        assert Party.objects.count() == 0

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert TenureRelationship.objects.count() == 0
        assert Party.objects.count() == 0
