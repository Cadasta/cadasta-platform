import os
import io
import pytest
from django.conf import settings
from django.test import TestCase
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.contenttypes.models import ContentType
from jsonattrs.models import Attribute, AttributeType, Schema
from jsonattrs.management.commands import loadattrtypes
from jsonattrs.models import create_attribute_types

from accounts.tests.factories import UserFactory
from core.tests.factories import PolicyFactory
from core.messages import SANITIZE_ERROR
from party.tests.factories import PartyFactory, TenureRelationshipFactory
from organization.tests.factories import ProjectFactory
from spatial.tests.factories import SpatialUnitFactory
from questionnaires.tests.factories import (QuestionnaireFactory,
                                            QuestionFactory,)

from party.models import Party, TenureRelationship
from organization.models import OrganizationRole
from resources.models import Resource
from spatial.models import SpatialUnit
from xforms.models import XFormSubmission
from xforms.mixins.model_helper import ModelHelper as mh
from xforms.exceptions import InvalidXMLSubmission

path = os.path.dirname(settings.BASE_DIR)


class XFormModelHelperTest(TestCase):
    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()
        create_attribute_types()

        loadattrtypes.Command().handle(force=True)

        self.user = UserFactory.create()
        self.project = ProjectFactory.create(
            current_questionnaire='a1')

        self.questionnaire = QuestionnaireFactory.create(
            id_string='a1', version=0, project=self.project, id='a1')
        QuestionFactory.create(
            name='location_geometry',
            label='Location of Parcel',
            type='GS',
            questionnaire=self.questionnaire)

        content_type_party = ContentType.objects.get(
            app_label='party', model='party')
        content_type_spatial = ContentType.objects.get(
            app_label='spatial', model='spatialunit')
        content_type_tenure = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        for content_type in [content_type_party, content_type_tenure,
                             content_type_spatial]:
            schema = Schema.objects.create(
                content_type=content_type,
                selectors=(self.project.organization.id, self.project.id, 'a1')
            )
            attr_type = AttributeType.objects.get(name='boolean')
            Attribute.objects.create(
                schema=schema,
                name='fname', long_name='True or False',
                attr_type=attr_type, index=0,
                required=False, omit=False
            )
            attr_type = AttributeType.objects.get(name='text')
            Attribute.objects.create(
                schema=schema,
                name='fname_two', long_name='Notes',
                attr_type=attr_type, index=1,
                required=False, omit=False
            )
        self.sanitizeable_questions = ['party_name', 'fname_two']
        OrganizationRole.objects.create(
            user=self.user, organization=self.project.organization)

    def test_sanitize_submission(self):
        geoshape = ('45.56342779158167 -122.67650283873081 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0;'
                    '45.56151562182025 -122.67490658909082 0.0 0.0;'
                    '45.563479432877415 -122.67494414001703 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0')
        data = {
            'id': 'a1',
            'meta': {
                'instanceID': 'uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad'
            },
            'version': str(self.questionnaire.version),
            'party_name': 'Party ⚽ One',
            'party_type': 'IN',
            'party_attributes_individual': {
                'fname': False,
                'fname_two': 'socks',
            },
            'party_photo': 'sad_birthday.png',
            'party_resource_invite': 'invitation.pdf',
            'location_type': 'BU',
            'location_geometry': geoshape,
            'location_attributes': {
                'fname': False,
                'fname_two': 'Location One',
            },
            'location_photo': 'resource_one.png',
            'location_resource_invite': 'resource_two.pdf',
            'tenure_type': 'CO',
            'tenure_relationship_attributes': {
                'fname': False,
                'fname_two': 'Tenure One'
            },
            'tenure_resource_photo': 'resource_three.png'
        }

        with pytest.raises(InvalidXMLSubmission) as e:
            mh.sanitize_submission(mh(), data, self.sanitizeable_questions)
        assert str(e.value) == SANITIZE_ERROR

    def test_sanitize_submission_with_error_in_group(self):
        geoshape = ('45.56342779158167 -122.67650283873081 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0;'
                    '45.56151562182025 -122.67490658909082 0.0 0.0;'
                    '45.563479432877415 -122.67494414001703 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0')
        data = {
            'id': 'a1',
            'meta': {
                'instanceID': 'uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad'
            },
            'version': str(self.questionnaire.version),
            'party_name': 'Party One',
            'party_type': 'IN',
            'party_attributes_individual': {
                'fname': False,
                'fname_two': 'soc⚽ks',
            },
            'party_photo': 'sad_birthday.png',
            'party_resource_invite': 'invitation.pdf',
            'location_type': 'BU',
            'location_geometry': geoshape,
            'location_attributes': {
                'fname': False,
                'fname_two': 'Location One',
            },
            'location_photo': 'resource_one.png',
            'location_resource_invite': 'resource_two.pdf',
            'tenure_type': 'CO',
            'tenure_relationship_attributes': {
                'fname': False,
                'fname_two': 'Tenure One'
            },
            'tenure_resource_photo': 'resource_three.png'
        }

        with pytest.raises(InvalidXMLSubmission) as e:
            mh.sanitize_submission(mh(), data, self.sanitizeable_questions)
        assert str(e.value) == SANITIZE_ERROR

    def test_sanitize_submission_with_negative_longitude(self):
        geoshape = ('-45.56342779158167 -122.67650283873081 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0;'
                    '45.56151562182025 -122.67490658909082 0.0 0.0;'
                    '45.563479432877415 -122.67494414001703 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0')
        data = {
            'id': 'a1',
            'meta': {
                'instanceID': 'uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad'
            },
            'version': str(self.questionnaire.version),
            'party_name': 'Party One',
            'party_type': 'IN',
            'party_attributes_individual': {
                'fname': False,
                'fname_two': 'socks',
            },
            'party_photo': 'sad_birthday.png',
            'party_resource_invite': 'invitation.pdf',
            'location_type': 'BU',
            'location_geometry': geoshape,
            'location_attributes': {
                'fname': False,
                'fname_two': 'Location One',
            },
            'location_photo': 'resource_one.png',
            'location_resource_invite': 'resource_two.pdf',
            'tenure_type': 'CO',
            'tenure_relationship_attributes': {
                'fname': False,
                'fname_two': 'Tenure One'
            },
            'tenure_resource_photo': 'resource_three.png'
        }

        try:
            mh.sanitize_submission(mh(), data, self.sanitizeable_questions)
        except InvalidXMLSubmission:
            assert False, "InvalidXMLSubmission raised unexpectedly"
        else:
            assert True

    def test_create_models(self):
        geoshape = ('45.56342779158167 -122.67650283873081 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0;'
                    '45.56151562182025 -122.67490658909082 0.0 0.0;'
                    '45.563479432877415 -122.67494414001703 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0')
        data = {
            'id': 'a1',
            'meta': {
                'instanceID': 'uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad'
            },
            'version': str(self.questionnaire.version),
            'party_name': 'Party One',
            'party_type': 'IN',
            'party_attributes_individual': {
                'fname': False,
                'fname_two': 'socks',
            },
            'party_photo': 'sad_birthday.png',
            'party_resource_invite': 'invitation.pdf',
            'location_type': 'BU',
            'location_geometry': geoshape,
            'location_attributes': {
                'fname': False,
                'fname_two': 'Location One',
            },
            'location_photo': 'resource_one.png',
            'location_resource_invite': 'resource_two.pdf',
            'tenure_type': 'CO',
            'tenure_relationship_attributes': {
                'fname': False,
                'fname_two': 'Tenure One'
            },
            'tenure_resource_photo': 'resource_three.png'
        }

        user = UserFactory.create()
        OrganizationRole.objects.create(
            user=user, organization=self.project.organization, admin=True)

        (questionnaire,
         parties, party_resources,
         locations, location_resources,
         tenure_relationships, tenure_resources) = mh.create_models(mh(),
                                                                    data,
                                                                    user)

        assert questionnaire == self.questionnaire
        party = Party.objects.get(name='Party One')
        assert parties == [party]
        assert party_resources[0]['id'] == party.id
        assert 'sad_birthday.png' in party_resources[0]['resources']
        assert 'invitation.pdf' in party_resources[0]['resources']

        location = SpatialUnit.objects.get(type='BU')
        assert locations == [location]
        assert location_resources[0]['id'] == location.id
        assert 'resource_two.pdf' in location_resources[0]['resources']

        tenure = TenureRelationship.objects.get(spatial_unit=location)
        assert tenure_relationships == [tenure]
        assert tenure.party == party
        assert tenure_resources[0]['id'] == tenure.id
        assert 'resource_three.png' in tenure_resources[0]['resources']

    def test_check_for_duplicate_submission(self):
        geoshape = ('45.56342779158167 -122.67650283873081 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0;'
                    '45.56151562182025 -122.67490658909082 0.0 0.0;'
                    '45.563479432877415 -122.67494414001703 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0')

        data = {
            'id': 'a1',
            'meta': {
                'instanceID': 'uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad'
            },
            'version': str(self.questionnaire.version),
            'party_repeat': [{
                'party_name': 'Party One',
                'party_type': 'IN',
                'party_attributes_individual': {
                    'fname': False,
                    'fname_two': 'socks',
                },
                'party_photo': 'sad_birthday.png',
                'party_resource_invite': 'invitation.pdf',

            }, {
                'party_name': 'Party Two',
                'party_type': 'GR',
                'party_attributes_group': {
                    'fname': True,
                    'fname_two': 'video games',
                },
                'party_photo': 'awesome_birthday.png',
                'party_resource_invite': 'invitation_two.pdf',

            }],
            'location_type': 'BU',
            'location_geometry': geoshape,
            'location_attributes': {
                'fname': False,
                'fname_two': 'Location One',
            },
            'location_photo': 'resource_one.png',
            'location_resource_invite': 'resource_two.pdf',
            'tenure_type': 'CO',
            'tenure_relationship_attributes': {
                'fname': False,
                'fname_two': 'Tenure One'
            },
            'tenure_resource_photo': 'resource_three.png'
        }

        assert not mh.check_for_duplicate_submission(
            mh(), data, self.questionnaire)

        party1 = PartyFactory.create(
            project=self.project,
            name='Party One',
            type='IN',
            attributes={
                'fname': False,
                'fname_two': 'socks',
            })

        party2 = PartyFactory.create(
            project=self.project,
            name='Party Two',
            type='GR',
            attributes={
                'fname': True,
                'fname_two': 'video games',
            })

        su = SpatialUnitFactory.create(
            project=self.project,
            type='BU',
            geometry=mh()._format_geometry(data),
            attributes={
                'fname': False,
                'fname_two': 'Location One'
            })

        tenure1 = TenureRelationshipFactory.create(
            project=self.project,
            spatial_unit=su,
            party=party1,
            tenure_type='CO',
            attributes={
                'fname': False,
                'fname_two': 'Tenure One'
            })

        tenure2 = TenureRelationshipFactory.create(
            project=self.project,
            spatial_unit=su,
            party=party2,
            tenure_type='CO',
            attributes={
                'fname': False,
                'fname_two': 'Tenure One'
            })

        xform = XFormSubmission.objects.create(
            json_submission={},
            user=self.user,
            questionnaire=self.questionnaire,
            instanceID='uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad')
        xform.parties.add(*[party1, party2])
        xform.spatial_units.add(su)
        xform.tenure_relationships.add(*[tenure1, tenure2])

        additional_resources = mh.check_for_duplicate_submission(
            mh(), data, self.questionnaire)

        (questionnaire,
         parties, party_resources,
         locations, location_resources,
         tenure_relationships, tenure_resources) = additional_resources

        assert Party.objects.all().count() == 2
        assert SpatialUnit.objects.all().count() == 1
        assert TenureRelationship.objects.all().count() == 2

        assert questionnaire == self.questionnaire

        assert party_resources[0]['id'] == party1.id
        assert party_resources[0]['resources'] == ['sad_birthday.png',
                                                   'invitation.pdf']
        assert party_resources[1]['id'] == party2.id
        assert party_resources[1]['resources'] == ['awesome_birthday.png',
                                                   'invitation_two.pdf']

        assert location_resources[0]['id'] == su.id
        assert location_resources[0]['resources'] == ['resource_one.png',
                                                      'resource_two.pdf']

        assert tenure_resources[0]['id'] == tenure1.id
        assert tenure_resources[0]['resources'] == ['resource_three.png']
        assert tenure_resources[1]['id'] == tenure2.id
        assert tenure_resources[1]['resources'] == ['resource_three.png']

    def test_create_party(self):
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # test without repeats
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        data = {
            'party_name': 'Party One',
            'party_type': 'IN',
            'party_attributes_individual': {
                'fname': False,
                'fname_two': 'socks',
            },
            'party_photo': 'sad_birthday.png',
            'party_resource_invite': 'invitation.pdf',
        }

        party_objects, party_resources = mh.create_party(
            mh(), data, self.project
        )
        assert len(party_objects) == 1
        party = Party.objects.get(name='Party One')
        assert party.type == 'IN'
        assert party.attributes == {'fname': False, 'fname_two': 'socks'}
        assert len(party_resources) == 1
        assert party_resources[0]['id'] == party.id
        assert len(party_resources[0]['resources']) == 2
        assert 'sad_birthday.png' in party_resources[0]['resources']
        assert 'invitation.pdf' in party_resources[0]['resources']
        assert party.project == self.project

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # test with repeats
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        data = {
            'party_repeat': [{
                'party_name': 'Party Two',
                'party_type': 'IN',
                'party_attributes_individual': {
                    'fname': False,
                    'fname_two': 'socks',
                },
                'party_photo': 'sad_birthday.png',
                'party_resource_invite': 'invitation.pdf',

            }, {
                'party_name': 'Party Three',
                'party_type': 'GR',
                'party_attributes_group': {
                    'fname': True,
                    'fname_two': 'video games',
                },
                'party_photo': 'awesome_birthday.png',
                'party_resource_invite': 'invitation_two.pdf',

            }]
        }
        party_objects, party_resources = mh.create_party(
            mh(), data, self.project
        )
        assert len(party_objects) == 2
        party = Party.objects.get(name='Party Two')
        assert party.type == 'IN'
        assert party.attributes == {'fname': False, 'fname_two': 'socks'}
        party2 = Party.objects.get(name='Party Three')
        assert party2.type == 'GR'
        assert party2.attributes == {
            'fname': True, 'fname_two': 'video games'}

        assert len(party_resources) == 2
        assert party_resources[0]['id'] == party.id
        assert len(party_resources[0]['resources']) == 2
        assert 'sad_birthday.png' in party_resources[0]['resources']
        assert 'invitation.pdf' in party_resources[0]['resources']
        assert party.project == self.project

        assert party_resources[1]['id'] == party2.id
        assert len(party_resources[1]['resources']) == 2
        assert 'awesome_birthday.png' in party_resources[1]['resources']
        assert 'invitation_two.pdf' in party_resources[1]['resources']
        assert party2.project == self.project

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # test without fails
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        data = {
            'party_nonsense': 'Blah blah blah',
            'party_type': 'IN',
            'party_attributes_individual': {
                'fname': False,
                'fname_two': 'socks',
            },
            'party_photo': 'sad_birthday.png',
            'party_resource_invite': 'invitation.pdf',
        }

        with pytest.raises(InvalidXMLSubmission):
            mh.create_party(
                mh(), data, self.project
            )
        assert Party.objects.count() == 3

    def test_create_spatial_unit(self):
        geoshape = ('45.56342779158167 -122.67650283873081 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0;'
                    '45.56151562182025 -122.67490658909082 0.0 0.0;'
                    '45.563479432877415 -122.67494414001703 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0')

        line = ('45.56342779158167 -122.67650283873081 0.0 0.0;'
                '45.56176327330353 -122.67669159919024 0.0 0.0;'
                '45.56151562182025 -122.67490658909082 0.0 0.0;')

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # test without repeats
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        data = {
            'location_type': 'BU',
            'location_geometry': geoshape,
            'location_attributes': {
                'fname': False,
                'fname_two': 'Location One',
            },
            'location_photo': 'resource.png',
            'location_resource_invite': 'resource_two.pdf',
        }

        location_objects, location_resources = mh.create_spatial_unit(
            mh(), data, self.project)
        assert len(location_objects) == 1
        location = SpatialUnit.objects.get(type='BU')
        assert location.attributes == {
            'fname': False, 'fname_two': 'Location One'}
        assert location.geometry.geom_type == 'Polygon'
        assert len(location_resources) == 1
        assert location_resources[0]['id'] == location.id
        assert len(location_resources[0]['resources']) == 2
        assert 'resource.png' in location_resources[0]['resources']
        assert 'resource_two.pdf' in location_resources[0]['resources']
        assert location.project == self.project

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # test with repeats
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        data = {
            'location_repeat': [{
                'location_type': 'PA',
                'location_geotrace': line,
                'location_attributes': {
                    'fname': False,
                    'fname_two': 'Location One',
                },
                'location_photo': 'resource.png',
                'location_resource_invite': 'resource_two.pdf',
            }, {
                'location_type': 'CB',
                'location_geoshape': geoshape,
                'location_attributes': {
                    'fname': True,
                    'fname_two': 'Location Two',
                },
                'location_photo': 'resource_three.png',
                'location_resource_invite': 'resource_four.pdf',
            }]
        }

        location_objects, location_resources = mh.create_spatial_unit(
            mh(), data, self.project)

        assert len(location_objects) == 2
        location = SpatialUnit.objects.get(type='PA')
        assert location.geometry.geom_type == 'LineString'
        assert location.attributes == {
            'fname': False, 'fname_two': 'Location One'}
        location2 = SpatialUnit.objects.get(type='CB')
        assert location2.geometry.geom_type == 'Polygon'
        assert location2.attributes == {
            'fname': True, 'fname_two': 'Location Two'}

        assert len(location_resources) == 2
        assert location_resources[0]['id'] == location.id
        assert len(location_resources[0]['resources']) == 2
        assert 'resource.png' in location_resources[0]['resources']
        assert 'resource_two.pdf' in location_resources[0]['resources']
        assert location.project == self.project

        assert location_resources[1]['id'] == location2.id
        assert len(location_resources[1]['resources']) == 2
        assert 'resource_three.png' in location_resources[1]['resources']
        assert 'resource_four.pdf' in location_resources[1]['resources']
        assert location2.project == self.project

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # test fails
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        data = {
            'location_nonsense': 'BLAH BLAH',
            'location_geometry': line,
            'location_attributes': {
                'fname': False,
                'fname_two': 'Location One',
            },
            'location_photo': 'resource.png',
            'location_resource_invite': 'resource_two.pdf',
        }

        with pytest.raises(InvalidXMLSubmission):
            mh.create_spatial_unit(
                mh(), data, self.project)
        assert SpatialUnit.objects.count() == 3

    def test_create_tenure_relationship(self):
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # test without repeats
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        party = PartyFactory.create(project=self.project)
        location = SpatialUnitFactory.create(project=self.project)

        data = {
            'tenure_type': 'CO',
            'tenure_relationship_attributes': {
                'fname': False,
                'fname_two': 'Tenure One'
            },
            'tenure_resource_photo': 'resource.png'
        }

        tenure_relationships, tenure_resources = mh.create_tenure_relationship(
            mh(), data, [party], [location], self.project)
        tenure = TenureRelationship.objects.get(tenure_type='CO')
        assert tenure_relationships == [tenure]
        assert tenure.party == party
        assert tenure.spatial_unit == location
        assert tenure.attributes == {'fname': False, 'fname_two': 'Tenure One'}
        assert len(tenure_resources) == 1
        assert tenure_resources[0]['id'] == tenure.id
        assert 'resource.png' in tenure_resources[0]['resources']

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # inside party_repeat
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        party2 = PartyFactory.create(project=self.project)
        party3 = PartyFactory.create(project=self.project)

        data = {
            'party_repeat': [{
                'tenure_type': 'WR',
                'tenure_relationship_attributes': {
                    'fname': False,
                    'fname_two': 'Tenure Two'
                },
                'tenure_resource_photo': 'resource_two.png'
            }, {
                'tenure_type': 'CO',
                'tenure_relationship_attributes': {
                    'fname': True,
                    'fname_two': 'Tenure Three'
                },
                'tenure_resource_photo': 'resource_three.png'
            }]
        }

        tenure_relationships, tenure_resources = mh.create_tenure_relationship(
            mh(), data, [party2, party3], [location], self.project)
        tenure2 = TenureRelationship.objects.get(party=party2)
        tenure3 = TenureRelationship.objects.get(party=party3)
        assert tenure_relationships == [tenure2, tenure3]

        assert tenure2.spatial_unit == location
        assert tenure2.tenure_type == 'WR'
        assert tenure2.attributes == {
            'fname': False, 'fname_two': 'Tenure Two'}

        assert tenure3.spatial_unit == location
        assert tenure3.tenure_type == 'CO'
        assert tenure3.attributes == {
            'fname': True, 'fname_two': 'Tenure Three'}

        assert len(tenure_resources) == 2
        assert tenure_resources[0]['id'] == tenure2.id
        assert 'resource_two.png' in tenure_resources[0]['resources']

        assert tenure_resources[1]['id'] == tenure3.id
        assert 'resource_three.png' in tenure_resources[1]['resources']

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # inside location_repeat
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        location2 = SpatialUnitFactory.create(project=self.project)
        location3 = SpatialUnitFactory.create(project=self.project)

        data = {
            'location_repeat': [{
                'tenure_type': 'WR',
                'tenure_relationship_attributes': {
                    'fname': False,
                    'fname_two': 'Tenure Four'
                },
                'tenure_resource_photo': 'resource_four.png'
            }, {
                'tenure_type': 'CO',
                'tenure_relationship_attributes': {
                    'fname': True,
                    'fname_two': 'Tenure Five'
                },
                'tenure_resource_photo': 'resource_five.png'
            }]
        }

        tenure_relationships, tenure_resources = mh.create_tenure_relationship(
            mh(), data, [party], [location2, location3], self.project)

        tenure4 = TenureRelationship.objects.get(spatial_unit=location2)
        tenure5 = TenureRelationship.objects.get(spatial_unit=location3)
        assert tenure_relationships == [tenure4, tenure5]

        assert tenure4.party == party
        assert tenure4.tenure_type == 'WR'
        assert tenure4.attributes == {
            'fname': False, 'fname_two': 'Tenure Four'}

        assert tenure5.party == party
        assert tenure5.tenure_type == 'CO'
        assert tenure5.attributes == {
            'fname': True, 'fname_two': 'Tenure Five'}

        assert len(tenure_resources) == 2
        assert tenure_resources[0]['id'] == tenure4.id
        assert 'resource_four.png' in tenure_resources[0]['resources']

        assert tenure_resources[1]['id'] == tenure5.id
        assert 'resource_five.png' in tenure_resources[1]['resources']

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # outside party_repeat
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        party4 = PartyFactory.create(project=self.project)
        party5 = PartyFactory.create(project=self.project)

        data = {
            'party_repeat': [],
            'tenure_type': 'CO',
            'tenure_relationship_attributes': {
                'fname': True,
                'fname_two': 'Tenure 6, 7'
            },
            'tenure_resource_photo': 'resource_six.png'
            }

        tenure_relationships, tenure_resources = mh.create_tenure_relationship(
            mh(), data, [party4, party5], [location], self.project)
        tenure6 = TenureRelationship.objects.get(party=party4)
        tenure7 = TenureRelationship.objects.get(party=party5)

        assert tenure_relationships == [tenure6, tenure7]
        assert tenure6.spatial_unit == location
        assert tenure6.tenure_type == 'CO'
        assert tenure6.attributes == {
            'fname': True, 'fname_two': 'Tenure 6, 7'}

        assert tenure7.spatial_unit == location
        assert tenure7.tenure_type == 'CO'
        assert tenure7.attributes == {
            'fname': True, 'fname_two': 'Tenure 6, 7'}

        assert len(tenure_resources) == 2
        assert tenure_resources[0]['id'] == tenure6.id
        assert 'resource_six.png' in tenure_resources[0]['resources']

        assert tenure_resources[1]['id'] == tenure7.id
        assert 'resource_six.png' in tenure_resources[1]['resources']

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # outside location_repeat
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        location4 = SpatialUnitFactory.create(project=self.project)
        location5 = SpatialUnitFactory.create(project=self.project)

        data = {
            'location_repeat': [],
            'tenure_type': 'WR',
            'tenure_relationship_attributes': {
                'fname': False,
                'fname_two': 'Tenure 8, 9'
            },
            'tenure_resource_photo': 'resource_seven.png'
        }

        tenure_relationships, tenure_resources = mh.create_tenure_relationship(
            mh(), data, [party], [location4, location5], self.project)

        tenure8 = TenureRelationship.objects.get(spatial_unit=location4)
        tenure9 = TenureRelationship.objects.get(spatial_unit=location5)
        assert tenure_relationships == [tenure8, tenure9]

        assert tenure8.party == party
        assert tenure8.tenure_type == 'WR'
        assert tenure8.attributes == {
            'fname': False, 'fname_two': 'Tenure 8, 9'}

        assert tenure9.party == party
        assert tenure9.tenure_type == 'WR'
        assert tenure9.attributes == {
            'fname': False, 'fname_two': 'Tenure 8, 9'}

        assert len(tenure_resources) == 2
        assert tenure_resources[0]['id'] == tenure8.id
        assert 'resource_seven.png' in tenure_resources[0]['resources']

        assert tenure_resources[1]['id'] == tenure9.id
        assert 'resource_seven.png' in tenure_resources[1]['resources']

        data = {
            'location_repeat': [],
            'tenure_nonsense': 'Blah blah blah',
            'tenure_relationship_attributes': {
                'fname': False,
                'fname_two': 'Tenure 8, 9'
            },
            'tenure_resource_photo': 'resource_seven.png'
        }

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # test failing
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        with pytest.raises(InvalidXMLSubmission):
            mh.create_tenure_relationship(
                mh(), data, [party], [location4, location5], self.project)
        assert TenureRelationship.objects.count() == 9

    def test_create_resource(self):
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # test attaching resources
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        file = open(
            path + '/xforms/tests/files/test_image_one.png', 'rb'
        ).read()

        data = InMemoryUploadedFile(
            file=io.BytesIO(file),
            field_name='test_image_one',
            name='{}.png'.format('test_image_one'),
            content_type='image/png',
            size=len(file),
            charset='utf-8',
        )
        party = PartyFactory.create(project=self.project)
        mh.create_resource(
            self, data, self.user, self.project, content_object=party)
        assert len(party.resources) == 1
        resource = Resource.objects.get(name='test_image_one.png')
        assert resource in party.resources

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # test attaching existing resources
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        party2 = PartyFactory.create(project=self.project)
        mh.create_resource(
            self, data, self.user, self.project, content_object=party2)

        assert Resource.objects.count() == 1
        assert len(party2.resources) == 1
        assert resource in party2.resources

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # test without content object
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        file = open(
            path + '/xforms/tests/files/test_image_two.png', 'rb'
        ).read()

        data = InMemoryUploadedFile(
            file=io.BytesIO(file),
            field_name='test_image_two',
            name='{}.png'.format('test_image_two'),
            content_type='image/png',
            size=len(file),
            charset='utf-8',
        )

        mh.create_resource(
            self, data, self.user, self.project, content_object=None)

        assert Resource.objects.count() == 2
        resource = Resource.objects.get(name='test_image_two.png')
        assert resource.content_objects.count() == 0

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        # test failing
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~
        with pytest.raises(InvalidXMLSubmission):
            mh.create_resource(
                self, data, self.user, self.project, content_object='ardvark')
        assert Resource.objects.count() == 2

    def test_format_repeat(self):
        data = {
            'party_type': 'Not repeating',
            'party_name': 'Still not repeating'
        }
        group = mh._format_repeat(self, data, ['party'])
        assert type(group) == list
        assert group[0] == data

        data = {
            'party_type': 'Repeating',
            'party_name': 'Totally repeating',
            'party_repeat': [{
                'repeat_type': 'Just One'
            }]
        }

        group = mh._format_repeat(self, data, ['party'])
        assert type(group) == list
        assert len(group) == 1
        assert group[0]['repeat_type'] == 'Just One'

        assert 'party_repeat' not in group
        assert 'party_type' not in group
        assert 'party_name' not in group

        data = {
            'party_type': 'Repeating',
            'party_name': 'Totally repeating',
            'party_repeat': [{
                'repeat_type': 'First!'
            }, {
                'repeat_type': 'Second!'
            }]
        }

        group = mh._format_repeat(self, data, ['party'])
        assert type(group) == list
        assert len(group) == 2
        assert group[0]['repeat_type'] == 'First!'
        assert group[1]['repeat_type'] == 'Second!'

        assert 'party_repeat' not in group
        assert 'party_type' not in group
        assert 'party_name' not in group

    def test_format_geometry(self):
        geoshape = ('45.56342779158167 -122.67650283873081 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0;'
                    '45.56151562182025 -122.67490658909082 0.0 0.0;'
                    '45.563479432877415 -122.67494414001703 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0')

        geotrace = ('45.56342779158167 -122.67650283873081 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0;'
                    '45.56151562182025 -122.67490658909082 0.0 0.0;'
                    '45.563479432877415 -122.67494414001703 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0;'
                    '45.56342779158167 -122.67650283873081 0.0 0.0;')

        line = ('45.56342779158167 -122.67650283873081 0.0 0.0;'
                '45.56176327330353 -122.67669159919024 0.0 0.0;'
                '45.56151562182025 -122.67490658909082 0.0 0.0;'
                '45.56181562182025 -122.67500658909082 0.0 0.0;')

        data = {
            'location_geometry': geoshape,
        }

        geom = mh()._format_geometry(data)
        assert 'POLYGON' in geom

        data = {
            'location_geoshape': geoshape,
        }

        geom = mh()._format_geometry(data)
        assert 'POLYGON' in geom

        data = {
            'location_geotrace': line,
        }

        geom = mh()._format_geometry(data)
        assert 'LINE' in geom

        data = {
            'location_geometry': geotrace,
        }

        geom = mh()._format_geometry(data)
        assert 'POLYGON' in geom

    def test_format_create_resource(self):
        party = PartyFactory.create(project=self.project)
        file_name = 'test_image_two.png'
        file = open(
            path + '/xforms/tests/files/test_image_two.png', 'rb'
        ).read()
        file_data = InMemoryUploadedFile(
            file=io.BytesIO(file),
            field_name='test_image_two',
            name=file_name,
            content_type='image/png',
            size=len(file),
            charset='utf-8',
        )
        files = {file_name: file_data}

        data = {
            'parties': [{'id': party.id, 'resources': [file_name]}],
            'locations': [{'id': '1234', 'resources': ['not_created.png']}]
        }

        mh()._format_create_resource(data, self.user, self.project,
                                     files, file_name,
                                     'parties', Party)

        assert Resource.objects.all().count() == 1
        resource = Resource.objects.get(name='test_image_two.png')
        assert resource in party.resources.all()

    def test_get_questionnaire(self):
        questionnaire = mh._get_questionnaire(
            self, 'a1', '0')
        assert questionnaire == self.questionnaire

        with pytest.raises(ValidationError):
            mh._get_questionnaire(
                self, 'bad_info', '0')

    def test_get_attributes(self):
        data = {
            'party_type': 'Party Type',
            'party_attributes_individual': {
                'name_indv': 'Party Indv Attrs',
                'type_indv': 'Party for one',
            },
            'party_attributes_people': {
                'name_ppl': 'Party People Attrs',
                'type_ppl': 'Where my party people at?',
            },
            'party_name': 'House Party'
        }
        attributes = mh._get_attributes(self, data, 'party')

        assert attributes['name_indv'] == 'Party Indv Attrs'
        assert attributes['type_indv'] == 'Party for one'
        assert attributes['name_ppl'] == 'Party People Attrs'
        assert attributes['type_ppl'] == 'Where my party people at?'
        assert 'party_name' not in attributes
        assert 'party_type' not in attributes

    def test_get_resource_files(self):
        data = {
            'ardvark': 'Ardvark!',
            'party_resource_thing': 'Party Resource Thing!',
            'location_resource_thing': 'Location Resource!',
            'party_photo': 'Party Photo!'
        }
        resources = mh._get_resource_files(self, data, 'party')
        assert type(resources) == list
        assert 'Party Resource Thing!' in resources
        assert 'Party Photo!' in resources

        assert 'Ardvark!' not in resources
        assert 'Location Resource!' not in resources

        resources = mh._get_resource_files(self, data, 'location')
        assert 'Location Resource!' in resources

        assert 'Ardvark!' not in resources
        assert 'Party Resource Thing!' not in resources
        assert 'Party Photo!' not in resources

    def test_get_resource_names(self):
        data = {
            'party_type': 'Party Type',
            'party_photo': 'Party Photo',
            'party_resource_thing': 'Party Resource Thing',
            'tenure_resource_thing': 'Tenure Resource Thing',
        }
        model = PartyFactory.create()
        resources = mh._get_resource_names(self, data, model, 'party')
        assert resources['id'] == model.id
        assert 'Party Photo' in resources['resources']
        assert 'Party Resource Thing' in resources['resources']

        assert 'Tenure Resource Thing' not in resources['resources']
        assert 'Party Type' not in resources['resources']

    def test_check_perm(self):
        with pytest.raises(PermissionDenied):
            mh._check_perm(mh, self.user, self.project)

        org_role = OrganizationRole.objects.get(
            user=self.user,
            organization=self.project.organization)
        org_role.admin = True
        org_role.save()

        try:
            mh._check_perm(mh, self.user, self.project)
        except PermissionDenied:
            self.fail("PermissionDenied raised unexpectedly")
