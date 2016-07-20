import os
import pytest
import json
from django.http import Http404
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.messages.api import get_messages
from django.contrib.contenttypes.models import ContentType

from buckets.test.utils import ensure_dirs
from buckets.test.storage import FakeS3Storage
from tutelary.models import Policy, assign_user_policies
from jsonattrs.models import Attribute, AttributeType, Schema

from organization.tests.factories import ProjectFactory
from core.tests.util import TestCase
from resources.tests.factories import ResourceFactory
from resources.forms import AddResourceFromLibraryForm, ResourceForm
from party.tests.factories import TenureRelationshipFactory
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


class LocationsListTest(TestCase):
    view = default.LocationsList
    template = 'spatial/location_map.html'

    def assign_policies(self):
        assign_policies(self.authorized_user)

    def set_up_models(self):
        self.project = ProjectFactory.create()
        self.locations = SpatialUnitFactory.create_batch(
            2, project=self.project)
        SpatialUnitFactory.create()

    def get_template_context(self):
        geojson = json.dumps(
            SpatialUnitGeoJsonSerializer(self.locations, many=True).data)
        return {
            'object': self.project,
            'object_list': self.locations,
            'geojson': geojson
        }

    def get_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def test_get_with_authorized_user(self):
        response, content = self.request(user=self.authorized_user)
        assert response.status_code == 200
        assert content == self.expected_content()

    def test_get_from_non_existend_project(self):
        with pytest.raises(Http404):
            self.request(user=self.authorized_user,
                         url_kwargs={'project': 'abc123'})

    def test_get_with_unauthorized_user(self):
        response, content = self.request(user=self.unauthorized_user)
        assert response.status_code == 200
        assert content == self.expected_content(
            geojson='{"type": "FeatureCollection", "features": []}')

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response['location']


class LocationAddTest(TestCase):
    view = default.LocationsAdd
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

    def set_up_models(self):
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

    def assign_policies(self):
        assign_policies(self.authorized_user)

    def get_template_context(self):
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

    def get_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def get_success_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'location': self.location_created.id
        }

    def test_get_with_authorized_user(self):
        response, content = self.request(user=self.authorized_user)
        assert response.status_code == 200
        assert content == self.expected_content()

    def test_get_from_non_existend_project(self):
        with pytest.raises(Http404):
            self.request(user=self.authorized_user,
                         url_kwargs={'project': 'abc123'})

    def test_get_with_unauthorized_user(self):
        response = self.request(user=self.unauthorized_user)
        assert response.status_code == 302
        assert ("You don't have permission to add "
                "locations to this project."
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response['location']

    def test_post_with_authorized_user(self):
        response = self.request(method='POST', user=self.authorized_user)
        assert SpatialUnit.objects.count() == 1
        self.location_created = SpatialUnit.objects.first()
        assert self.location_created.attributes.get('fname') == 'Test text'
        assert response.status_code == 302
        assert response['location'] == self.expected_success_url

    def test_post_with_unauthorized_user(self):
        response = self.request(method='POST', user=self.unauthorized_user)
        assert SpatialUnit.objects.count() == 0
        assert response.status_code == 302
        assert ("You don't have permission to add "
                "locations to this project."
                in [str(m) for m in get_messages(self.request)])

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert SpatialUnit.objects.count() == 0
        assert response.status_code == 302
        assert '/account/login/' in response['location']


class LocationDetailTest(TestCase):
    view = default.LocationDetail
    template = 'spatial/location_detail.html'

    def set_up_models(self):
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

    def assign_policies(self):
        assign_policies(self.authorized_user)

    def get_template_context(self):
        return {
            'object': self.project,
            'location': self.location,
            'geojson': '{"type": "FeatureCollection", "features": []}',
            'attributes': (('Test field', 'test', ), )
        }

    def get_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'location': self.location.id
        }

    def test_get_with_authorized_user(self):
        response, content = self.request(user=self.authorized_user)
        assert response.status_code == 200
        assert content == self.expected_content()

    def test_get_from_non_existend_project(self):
        with pytest.raises(Http404):
            self.request(user=self.authorized_user,
                         url_kwargs={'project': 'abc123'})

    def test_get_non_existend_location(self):
        with pytest.raises(Http404):
            self.request(user=self.authorized_user,
                         url_kwargs={'location': 'abc123'})

    def test_get_with_unauthorized_user(self):
        response = self.request(user=self.unauthorized_user)
        assert response.status_code == 302
        assert ("You don't have permission to view this location."
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response['location']


class LocationEditTest(TestCase):
    view = default.LocationEdit
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

    def set_up_models(self):
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

    def assign_policies(self):
        assign_policies(self.authorized_user)

    def get_template_context(self):
        return {'object': self.project,
                'location': self.location,
                'form': forms.LocationForm(instance=self.location),
                'geojson': '{"type": "FeatureCollection", "features": []}'}

    def get_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'location': self.location.id
        }

    def get_success_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'location': self.location.id
        }

    def test_get_with_authorized_user(self):
        response, content = self.request(user=self.authorized_user)
        assert response.status_code == 200
        assert content == self.expected_content()

    def test_get_from_non_existend_project(self):
        with pytest.raises(Http404):
            self.request(user=self.authorized_user,
                         url_kwargs={'project': 'abc123'})

    def test_get_non_existend_location(self):
        with pytest.raises(Http404):
            self.request(user=self.authorized_user,
                         url_kwargs={'location': 'abc123'})

    def test_get_with_unauthorized_user(self):
        response = self.request(user=self.unauthorized_user)
        assert response.status_code == 302
        assert ("You don't have permission to update this location."
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response['location']

    def test_post_with_authorized_user(self):
        response = self.request(method='POST', user=self.authorized_user)
        assert response.status_code == 302
        assert response['location'] == self.expected_success_url

        self.location.refresh_from_db()
        assert self.location.type == self.post_data['type']
        assert self.location.attributes.get('fname') == 'New text'

    def test_post_with_unauthorized_user(self):
        response = self.request(method='POST', user=self.unauthorized_user)
        assert response.status_code == 302
        assert ("You don't have permission to update this location."
                in [str(m) for m in get_messages(self.request)])
        self.location.refresh_from_db()
        assert self.location.type != self.post_data['type']

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response['location']
        self.location.refresh_from_db()
        assert self.location.type != self.post_data['type']


class LocationDelete(TestCase):
    view = default.LocationDelete
    template = 'spatial/location_delete.html'
    success_url_name = 'locations:list'
    post_data = {}

    def set_up_models(self):
        self.project = ProjectFactory.create()
        self.location = SpatialUnitFactory.create(project=self.project)
        TenureRelationshipFactory.create(
            project=self.project, spatial_unit=self.location)

    def assign_policies(self):
        assign_policies(self.authorized_user)

    def get_template_context(self):
        return {'object': self.project,
                'location': self.location,
                'geojson': '{"type": "FeatureCollection", "features": []}'}

    def get_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'location': self.location.id
        }

    def get_success_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def test_get_with_authorized_user(self):
        response, content = self.request(user=self.authorized_user)
        assert response.status_code == 200
        assert content == self.expected_content()

    def test_get_from_non_existend_project(self):
        with pytest.raises(Http404):
            self.request(user=self.authorized_user,
                         url_kwargs={'project': 'abc123'})

    def test_get_non_existend_location(self):
        with pytest.raises(Http404):
            self.request(user=self.authorized_user,
                         url_kwargs={'location': 'abc123'})

    def test_get_with_unauthorized_user(self):
        response = self.request(user=self.unauthorized_user)
        assert response.status_code == 302
        assert ("You don't have permission to remove this location."
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response['location']

    def test_post_with_authorized_user(self):
        response = self.request(method='POST', user=self.authorized_user)
        assert response.status_code == 302
        assert response['location'] == self.expected_success_url

        assert SpatialUnit.objects.count() == 0
        assert TenureRelationship.objects.count() == 0

    def test_post_with_unauthorized_user(self):
        response = self.request(method='POST', user=self.unauthorized_user)
        assert response.status_code == 302
        assert ("You don't have permission to remove this location."
                in [str(m) for m in get_messages(self.request)])
        assert SpatialUnit.objects.count() == 1
        assert TenureRelationship.objects.count() == 1

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response['location']
        assert SpatialUnit.objects.count() == 1
        assert TenureRelationship.objects.count() == 1


class LocationResourceAddTest(TestCase):
    view = default.LocationResourceAdd
    template = 'spatial/resources_add.html'
    success_url_name = 'locations:detail'

    def set_up_models(self):
        self.project = ProjectFactory.create()
        self.location = SpatialUnitFactory.create(project=self.project)
        self.assigned = ResourceFactory.create(project=self.project,
                                               content_object=self.location)
        self.unassigned = ResourceFactory.create(project=self.project)

    def assign_policies(self):
        assign_policies(self.authorized_user)

    def get_template_context(self):
        form = AddResourceFromLibraryForm(content_object=self.location,
                                          project_id=self.project.id)
        return {'object': self.project,
                'location': self.location,
                'form': form,
                'geojson': '{"type": "FeatureCollection", "features": []}'}

    def get_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'location': self.location.id
        }

    def get_success_url_kwargs(self):
        return self.get_url_kwargs()

    def get_post_data(self):
        return {
            self.assigned.id: False,
            self.unassigned.id: True,
        }

    def test_get_with_authorized_user(self):
        response, content = self.request(user=self.authorized_user)
        assert response.status_code == 200
        assert content == self.expected_content()

    def test_get_from_non_existend_project(self):
        with pytest.raises(Http404):
            self.request(user=self.authorized_user,
                         url_kwargs={'project': 'abc123'})

    def test_get_non_existend_location(self):
        with pytest.raises(Http404):
            self.request(user=self.authorized_user,
                         url_kwargs={'location': 'abc123'})

    def test_get_with_unauthorized_user(self):
        response = self.request(user=self.unauthorized_user)
        assert response.status_code == 302
        assert ("You don't have permission to "
                "add resources to this location."
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response['location']

    def test_post_with_authorized_user(self):
        response = self.request(method='POST', user=self.authorized_user)
        assert response.status_code == 302
        assert response['location'] == self.expected_success_url + '#resources'

        assert self.location.resources.count() == 1
        assert self.location.resources.first() == self.unassigned

    def test_post_with_unauthorized_user(self):
        response = self.request(method='POST', user=self.unauthorized_user)
        assert response.status_code == 302
        assert ("You don't have permission to "
                "add resources to this location."
                in [str(m) for m in get_messages(self.request)])
        assert self.location.resources.count() == 1
        assert self.location.resources.first() == self.assigned

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response['location']
        assert self.location.resources.count() == 1
        assert self.location.resources.first() == self.assigned


class LocationResourceNewTest(TestCase):
    view = default.LocationResourceNew
    template = 'spatial/resources_new.html'
    success_url_name = 'locations:detail'

    def set_up_models(self):
        self.project = ProjectFactory.create()
        self.location = SpatialUnitFactory.create(project=self.project)

    def assign_policies(self):
        assign_policies(self.authorized_user)

    def get_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'location': self.location.id
        }

    def get_success_url_kwargs(self):
        return self.get_url_kwargs()

    def get_template_context(self):
        form = ResourceForm(content_object=self.location,
                            project_id=self.project.id)
        return {'object': self.project,
                'location': self.location,
                'form': form,
                'geojson': '{"type": "FeatureCollection", "features": []}'}

    def get_post_data(self):
        path = os.path.dirname(settings.BASE_DIR)
        ensure_dirs(add='s3/uploads/resources')
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/image.jpg', 'rb').read()
        file_name = storage.save('image.jpg', file)

        return {
            'name': 'Some name',
            'description': '',
            'file': file_name,
            'original_file': 'image.png',
            'mime_type': 'image/jpeg'
        }

    def test_get_with_authorized_user(self):
        response, content = self.request(user=self.authorized_user)
        assert response.status_code == 200
        assert content == self.expected_content()

    def test_get_from_non_existend_project(self):
        with pytest.raises(Http404):
            self.request(user=self.authorized_user,
                         url_kwargs={'project': 'abc123'})

    def test_get_non_existend_location(self):
        with pytest.raises(Http404):
            self.request(user=self.authorized_user,
                         url_kwargs={'location': 'abc123'})

    def test_get_with_unauthorized_user(self):
        response = self.request(user=self.unauthorized_user)
        assert response.status_code == 302
        assert ("You don't have permission to "
                "add resources to this location."
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response['location']

    def test_post_with_authorized_user(self):
        response = self.request(method='POST', user=self.authorized_user)
        assert response.status_code == 302
        assert response['location'] == self.expected_success_url + '#resources'

        assert self.location.resources.count() == 1

    def test_post_with_unauthorized_user(self):
        response = self.request(method='POST', user=self.unauthorized_user)
        assert response.status_code == 302
        assert ("You don't have permission to "
                "add resources to this location."
                in [str(m) for m in get_messages(self.request)])
        assert self.location.resources.count() == 0

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response['location']
        assert self.location.resources.count() == 0


class TenureRelationshipAddTest(TestCase):
    view = default.TenureRelationshipAdd
    template = 'spatial/relationship_add.html'
    success_url_name = 'locations:detail'

    def assign_policies(self):
        assign_policies(self.authorized_user)

    def set_up_models(self):
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

    def get_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'location': self.spatial_unit.id
        }

    def get_success_url_kwargs(self):
        return self.get_url_kwargs()

    def get_post_data(self):
        return {
            'new_entity': 'on',
            'id': '',
            'name': 'The Beatles',
            'party_type': 'GR',
            'tenure_type': 'CU',
            'party::p_name': 'Party Name',
            'relationship::r_name': 'Rel Name'
        }

    def get_template_context(self):
        return {'object': self.project,
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
                    )),
                'geojson': json.dumps(SpatialUnitGeoJsonSerializer(
                    [self.spatial_unit], many=True).data)
                }

    def test_get_with_authorized_user(self):
        response, content = self.request(user=self.authorized_user)
        assert response.status_code == 200
        assert content == self.expected_content()

    def test_get_from_non_existend_project(self):
        with pytest.raises(Http404):
            self.request(user=self.authorized_user,
                         url_kwargs={'project': 'abc123'})

    def test_get_non_existend_location(self):
        with pytest.raises(Http404):
            self.request(user=self.authorized_user,
                         url_kwargs={'location': 'abc123'})

    def test_get_with_unauthorized_user(self):
        response = self.request(user=self.unauthorized_user)
        assert response.status_code == 302
        assert ("You don't have permission to add tenure relationships to "
                "this project."
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response['location']

    def test_post_with_authorized(self):
        response = self.request(method='POST', user=self.authorized_user)
        assert response.status_code == 302
        assert (response['location'] ==
                self.expected_success_url + '#relationships')

        assert TenureRelationship.objects.count() == 1
        rel = TenureRelationship.objects.first()
        assert rel.attributes.get('r_name') == 'Rel Name'
        assert Party.objects.count() == 1
        party = Party.objects.first()
        assert party.attributes.get('p_name') == 'Party Name'

    def test_post_with_authorized_invalid_data(self):
        response, content = self.request(method='POST',
                                         user=self.authorized_user,
                                         data={'name': ''})
        assert response.status_code == 200
        context = self.get_template_context()
        data = self.get_post_data()
        data['name'] = ''
        context['form'] = forms.TenureRelationshipForm(
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
        expected = render_to_string(
            self.template, context, request=self.request)
        assert content == expected

        assert TenureRelationship.objects.count() == 0
        assert Party.objects.count() == 0

    def test_post_with_unauthorized_user(self):
        response = self.request(method='POST', user=self.unauthorized_user)
        assert response.status_code == 302
        assert ("You don't have permission to add tenure relationships to "
                "this project."
                in [str(m) for m in get_messages(self.request)])
        assert TenureRelationship.objects.count() == 0
        assert Party.objects.count() == 0

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response['location']
        assert TenureRelationship.objects.count() == 0
        assert Party.objects.count() == 0
