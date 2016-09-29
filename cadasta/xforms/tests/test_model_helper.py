'''
create_models
    Is the questionnaire the current_questionnaire?
create_party
    Is a party created?
    Is the right number of parties created?
    is a dictionnairy of their IDs and resources connected?
create_spatial_unit
    Is a spatial unit created?
    Is the right number of spatial units created?
    is a dictionnairy of their IDs and resources connected?
create_tenure_relationship
    Is a tenure relationship created?
    Is the right number of tenure relationships created?
    Are they connected to the correct party/spatial unit?
    is a dictionnairy of their IDs and resources connected?
create_resource
    Does it take a file submitted and save it as a Resource?
    Does it save it to the correct su/party/tenure?
    If the file has already been read, does it create a
        new content object for an existing resource?
upload_submission_data
    Does it check to see if there is an xml_submission_file?
    Does it get the appropraite resources for each su/p/t?
    Does it return an XFormSubmission object?
upload_resource_files
    Does it match the appropriate resource with the appropriate content_object?
    What happens if the resources have the same name?
_format_geometry
    Does it fix the geoshape issue?
    Are lines appropriately labeled?
    Are points appropriately labeled?
    Are polygons appropriately labeled?
_format_repeat
    If there's a repeat, does it return the repeat group?
    If there's only one object in the repeat group, does it
        convert it to a list?
_get_questionnaire
    Does it return the questionnaire?
    If there isn't a questionnaire, does it return an error?
_get_attributes
    Does it collect attributes from all of the attribute groups?
_get_resource_files
    Does it collect both _resource and _photo?
_get_resource_name
    Does it collect both _resource and _photo?
    Does it connect them to the correct object?

'''

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from jsonattrs.models import Attribute, AttributeType, Schema
from jsonattrs.management.commands import loadattrtypes

from party.tests.factories import PartyFactory
from party.models import Party
from organization.tests.factories import ProjectFactory
from xforms.mixins.model_helper import ModelHelper as mh
from questionnaires.tests.factories import QuestionnaireFactory
from questionnaires.models import Questionnaire


class XFormModelHelperTest(TestCase):
    def test_create_models(self):
        mh.create_models(self, data)

    def test_create_party(self):
        loadattrtypes.Command().handle(force=True)
        self.project = ProjectFactory.create(current_questionnaire='a1')
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(self.project.organization.id, self.project.id, 'a1'))
        attr_type = AttributeType.objects.get(name='boolean')
        Attribute.objects.create(
            schema=schema,
            name='balloons', long_name='Ballons?',
            attr_type=attr_type, index=0,
            required=False, omit=False
        )
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='presents', long_name='Presents?',
            attr_type=attr_type, index=1,
            required=False, omit=False
        )
        data = {
            'party_name': 'Party One',
            'party_type': 'IN',
            'party_attributes_individual': {
                'balloons': False,
                'presents': 'socks',
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
        assert party.attributes == {'balloons': False, 'presents': 'socks'}
        assert len(party_resources) == 1
        assert party_resources[0]['id'] == party.id
        assert len(party_resources[0]['resources']) == 2
        assert 'sad_birthday.png' in party_resources[0]['resources']
        assert 'invitation.pdf' in party_resources[0]['resources']
        assert party.project == self.project

        data = {
            'party_repeat': [{
                'party_name': 'Party Two',
                'party_type': 'IN',
                'party_attributes_individual': {
                    'balloons': False,
                    'presents': 'socks',
                },
                'party_photo': 'sad_birthday.png',
                'party_resource_invite': 'invitation.pdf',

            }, {
                'party_name': 'Party Three',
                'party_type': 'GR',
                'party_attributes_group': {
                    'balloons': True,
                    'presents': 'video games',
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
        assert party.attributes == {'balloons': False, 'presents': 'socks'}
        party2 = Party.objects.get(name='Party Three')
        assert party2.type == 'GR'
        assert party2.attributes == {
            'balloons': True, 'presents': 'video games'}

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

    def test_create_spatial_unit(self):
        mh.create_spatial_unit(self, data, project, questionnaire, party)

    def test_create_tenure_relationship(self):
        mh.create_tenure_relationship(self, data, party, location, project)

    def test_create_resource(self):
        mh.create_resource(self, data, user, project, content_object)

    def test_upload_submission_data(self):
        mh.upload_submission_data(self, request)

    def test_upload_resource_files(self):
        mh.upload_resource_files(self, request, data)

    def test_format_geometry(self):
        point = '40.6890612 -73.9925067 0.0 0.0;'
        geometry = mh._format_geometry(self, point, False)
        assert 'POINT' in geometry

        point_minus_semi = '340.6890612 -373.9925067 0.0 0.0'
        geometry = mh._format_geometry(self, point_minus_semi, False)
        assert 'POINT' in geometry

        polygon = ('40.6890612 -73.9925067 0.0 0.0;'
                   '41.6890612 -73.9925067 0.0 0.0;'
                   '41.6890612 -72.9925067 0.0 0.0;'
                   '40.6890612 -72.9925067 0.0 0.0;'
                   '40.6890612 -73.9925067 0.0 0.0;')
        geometry = mh._format_geometry(self, polygon, False)
        assert 'POLYGON' in geometry

        line = ('45.56342779158167 -122.67650283873081 0.0 0.0;'
                '45.56176327330353 -122.67669159919024 0.0 0.0;'
                '45.56151562182025 -122.67490658909082 0.0 0.0;')
        geometry = mh._format_geometry(self, line, False)
        assert 'LINESTRING' in geometry

        geoshape = ('45.56342779158167 -122.67650283873081 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0;'
                    '45.56151562182025 -122.67490658909082 0.0 0.0;'
                    '45.563479432877415 -122.67494414001703 0.0 0.0;'
                    '45.56176327330353 -122.67669159919024 0.0 0.0')
        geometry = mh._format_geometry(self, geoshape, True)
        assert 'POLYGON' in geometry

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


    def test_get_questionnaire(self):
        self.quest = QuestionnaireFactory.create(
            id_string='questionnaire', version=0)

        questionnaire = mh._get_questionnaire(
            self, 'questionnaire', '0')
        assert questionnaire == self.quest
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
