import pytest
from django.test import TestCase
from core.messages import SANITIZE_ERROR
from ..exceptions import InvalidQuestionnaire
from .. import validators


class FilterTest(TestCase):
    def test_filter_required(self):
        assert validators.filter_required({'name': 'location_type'}) is True
        assert validators.filter_required({'name': 'party_type'}) is True
        assert validators.filter_required({'name': 'party_name'}) is True
        assert validators.filter_required({'name': 'tenure_type'}) is True
        assert validators.filter_required(
            {'name': 'location_geoshape'}) is True
        assert validators.filter_required(
            {'name': 'location_geotrace'}) is True
        assert validators.filter_required(
            {'name': 'location_geometry'}) is True
        assert validators.filter_required({'name': 'other_field'}) is False

    def test_filter_geometries(self):
        assert validators.filter_geometries(
            {'name': 'location_geoshape'}) is True
        assert validators.filter_geometries(
            {'name': 'location_geotrace'}) is True
        assert validators.filter_geometries(
            {'name': 'location_geometry'}) is True
        assert validators.filter_geometries(
            {'name': 'other_field'}) is False


class IsRequiredTest(TestCase):
    def test(self):
        assert validators.is_required({'required': 'yes'}) is True
        assert validators.is_required({'required': 'no'}) is False
        assert validators.is_required(None) is False


class FlattenTest(TestCase):
    def test(self):
        fields = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'text',
             'bind': {'required': 'no'}},
        ]
        flat = validators.flatten(fields)
        assert flat == {
            'location_type': ('select one', True),
            'party_type': ('text', False)
        }


class ValidateRequiredTest(TestCase):
    available_fields = {
        'valid': ('text', True),
        'wrong_type': ('text', True),
        'not_required': ('text', False),
    }

    field_def = {
        'valid': 'text',
        'not_present': 'text',
        'wrong_type': 'select one',
        'not_required': 'text',
    }

    def test_valid(self):
        error = validators.validate_field(self.field_def,
                                          self.available_fields,
                                          'valid')
        assert error is None

    def test_required_field_not_provided(self):
        error = validators.validate_field(self.field_def,
                                          self.available_fields,
                                          'not_present')
        assert error == 'Field not_present is required.'

    def test_wrong_type(self):
        error = validators.validate_field(self.field_def,
                                          self.available_fields,
                                          'wrong_type')
        assert error == 'Field wrong_type must be of type select one.'

    def test_not_required(self):
        error = validators.validate_field(self.field_def,
                                          self.available_fields,
                                          'not_required')
        assert error == 'Field not_required must be required.'


class CheckRequiredFieldsTest(TestCase):
    def test_validate_required_valid(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'geoshape',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        try:
            validators.validate_required(data)
        except InvalidQuestionnaire:
            assert False, "InvalidQuestionnaire raised unexpectedly"
        else:
            assert True

    def test_validate_required__party_name(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'geoshape',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__party_name_not_required(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_name'},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'geoshape',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__party_name_wrong_type(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'geoshape',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__party_type(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'geoshape',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__party_type_not_required(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type'},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'geoshape',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__party_type_wrong_type(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'geoshape',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__location_type(self):
        data = [
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'geoshape',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__location_type_not_required(self):
        data = [
            {'name': 'location_type'},
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'geoshape',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__location_type_wrong_type(self):
        data = [
            {'name': 'location_type',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'geoshape',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__tenure_type(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'geoshape',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__tenure_type_not_required(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one'},
            {'name': 'location_geoshape',
             'type': 'geoshape',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__tenure_type_wrong_type(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'geoshape',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__location_field(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__location_field_not_required(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'geoshape'},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__location_field_wrong_type(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__one_location_field_not_required(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type', 'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'geoshape'},
            {'name': 'location_geotrace',
             'type': 'geotrace',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required__one_location_field_wrong_type(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type', 'bind': {'required': 'yes'}},
            {'name': 'party_name',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'tenure_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'location_geoshape',
             'type': 'text',
             'bind': {'required': 'yes'}},
            {'name': 'location_geotrace',
             'type': 'geotrace',
             'bind': {'required': 'yes'}},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)

    def test_validate_required_valid_with_repeat(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'type': 'repeat',
             'children': [{'name': 'party_name',
                           'type': 'text',
                           'bind': {'required': 'yes'}},
                          {'name': 'tenure_type',
                           'type': 'select one',
                           'bind': {'required': 'yes'}}]},
            {'type': 'repeat',
             'children': [{'name': 'location_geoshape',
                           'type': 'geoshape',
                           'bind': {'required': 'yes'}}]},
            {'name': 'other_field'}
        ]
        try:
            validators.validate_required(data)
        except InvalidQuestionnaire:
            assert False, "InvalidQuestionnaire raised unexpectedly"
        else:
            assert True

    def test_validate_required_error_in_repeat(self):
        data = [
            {'name': 'location_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'name': 'party_type',
             'type': 'select one',
             'bind': {'required': 'yes'}},
            {'type': 'repeat',
             'children': [{'name': 'party_name',
                           'type': 'text',
                           'bind': {'required': 'yes'}},
                          {'name': 'tenure_type',
                           'type': 'select one',
                           'bind': {'required': 'yes'}}]},
            {'type': 'repeat',
             'children': [{'name': 'location_geoshape',
                           'type': 'text',
                           'bind': {'required': 'yes'}}]},
            {'name': 'other_field'}
        ]
        with pytest.raises(InvalidQuestionnaire):
            validators.validate_required(data)


class ValidateAccuracyTest(TestCase):
    def test_positive_float(self):
        assert validators.validate_accuracy(1.5) is True
        assert validators.validate_accuracy('1.5') is True
        assert validators.validate_accuracy(1) is True
        assert validators.validate_accuracy('1') is True

    def test_negative_float(self):
        assert validators.validate_accuracy(-1.5) is False
        assert validators.validate_accuracy('-1.5') is False
        assert validators.validate_accuracy(-1) is False
        assert validators.validate_accuracy('-1') is False

    def test_wrong_type(self):
        assert validators.validate_accuracy(True) is False
        assert validators.validate_accuracy('Something') is False


class GpsRelevantTest(TestCase):
    def test_gps_relevant(self):
        assert validators.gps_relevant({'type': 'GP'}) is True
        assert validators.gps_relevant({'type': 'IN'}) is False


class ValidateTypeTest(TestCase):
    def test_validate_string(self):
        assert validators.validate_type('string', 'akshdk') is True
        assert validators.validate_type('string', 1) is False
        assert validators.validate_type('string', True) is False
        assert validators.validate_type('string', []) is False

    def test_validate_number(self):
        assert validators.validate_type('number', 'akshdk') is False
        assert validators.validate_type('number', 1) is True
        assert validators.validate_type('number', True) is False
        assert validators.validate_type('number', []) is False

    def test_validate_boolean(self):
        assert validators.validate_type('boolean', 'akshdk') is False
        assert validators.validate_type('boolean', 1) is False
        assert validators.validate_type('boolean', True) is True
        assert validators.validate_type('boolean', []) is False

    def test_validate_array(self):
        assert validators.validate_type('array', 'akshdk') is False
        assert validators.validate_type('array', 1) is False
        assert validators.validate_type('array', True) is False
        assert validators.validate_type('array', []) is True


class ValidateIDStringTest(TestCase):
    def test_validate_id_string_missing(self):
        data = {'id_string': ''}
        assert validators.validate_id_string(data) == (
            "'id_string' cannot be blank or contain whitespace.")

    def test_validate_id_string_valid(self):
        data = {'id_string': 'yx8sqx6488wbc4yysnkrbnfq'}
        assert validators.validate_id_string(data) is None

    def test_validate_id_string_contains_whitespace(self):
        data = {'id_string': 'yx8sqx6488wbc4yys nkrbnfq'}
        assert validators.validate_id_string(data) == (
            "'id_string' cannot be blank or contain whitespace.")


def positive(val):
    return val > 0


class ValidateSchemaTest(TestCase):
    SCHEMA = {
        'title': {
            'type': 'string',
            'required': True
        },
        'id_string': {
            'type': 'string',
            'required': True
        },
        'some_list': {
            'type': 'string',
            'enum': ['A', 'B', 'C']
        },
        'no_code': {
            'type': 'string'
        },
        'function': {
            'type': 'number',
            'function': positive,
        },
        'function2': {
            'type': 'number',
            'function': positive,
            'errors': {
                'function': "Number must be positive"
            }
        }
    }

    def test_valid_schema(self):
        data = {
            'title': 'Title',
            'id_string': 'askljdaskljdl',
            'some_list': 'A'
        }
        assert validators.validate_schema(self.SCHEMA, data) == {}

    def test_invalid_schema(self):
        data = {
            'id_string': 123,
            'some_list': 'D',
            'no_code': '<GotCode>',
            'function': -1,
            'function2': -1,
        }
        errors = validators.validate_schema(self.SCHEMA, data)
        assert 'This field is required.' in errors['title']
        assert 'Value must be of type string.' in errors['id_string']
        assert 'D is not an accepted value.' in errors['some_list']
        assert SANITIZE_ERROR in errors['no_code']
        assert 'Validator positive did not validate.' in errors['function']
        assert 'Number must be positive' in errors['function2']

    def test_validate_with_relevant(self):
        def rel(json):
            return json.get('text') == 'John'

        schema = {
            'text': {'type': 'string'},
            'number': {'type': 'number', 'relevant': rel}
        }

        errors = validators.validate_schema(
            schema, {'text': 'John', 'number': 'Ringo'})
        assert 'number' in errors

        errors = validators.validate_schema(
            schema, {'text': 'Paul', 'number': 'Ringo'})
        assert 'number' not in errors


class QuestionnaireTestCase(TestCase):
    def test_valid_questionnaire(self):
        data = {
            'title': 'yx8sqx6488wbc4yysnkrbnfq',
            'id_string': 'yx8sqx6488wbc4yysnkrbnfq',
            'default_language': 'en',
            'questions': [{
                'name': "start",
                'label': None,
                'type': "ST",
                'required': False,
                'constraint': None,
                'index': 0
            }]
        }
        errors = validators.validate_questionnaire(data)
        assert errors is None

    def test_invalid_questionnaire(self):
        data = {
            'questions': [{
                'label': None,
                'type': "ST",
                'required': False,
                'constraint': None,
                'index': 0
            }],
            'question_groups': [{
                'label': 'A group',
                'index': 0
            }]
        }
        errors = validators.validate_questionnaire(data)
        assert 'This field is required.' in errors['title']
        assert 'This field is required.' in errors['id_string']
        assert 'This field is required.' in errors['questions'][0]['name']
        assert ('This field is required.' in
                errors['question_groups'][0]['name'])

    def test_invalid_id_string(self):
        data = {
            'title': 'yx8sqx6488wbc4yysnkrbnfq',
            'id_string': 'yx8sqx6488w bc4yysnkrbnfq',
            'default_language': 'en',
            'questions': [{
                'name': "start",
                'label': None,
                'type': "ST",
                'required': False,
                'constraint': None,
                'index': 0
            }]
        }
        errors = validators.validate_questionnaire(data)
        assert ("'id_string' cannot be blank or contain whitespace." in
                errors['id_string'])


class QuestionGroupTestCase(TestCase):
    def test_valid_questiongroup(self):
        data = [{
            'name': "location_attributes",
            'label': "Location Attributes",
            'type': 'group',
            'index': 0,
            'questions': [{
                'name': "start",
                'label': 'Start',
                'type': "ST",
                'index': 0
            }]
        }]
        errors = validators.validate_question_groups(data)
        assert errors == [{}]

    def test_invalid_questiongroup(self):
        data = [{
            'label': "location attributes",
            'type': 'group',
            'index': 0,
            'questions': [{
                'label': 'Start',
                'type': "ST",
                'index': 0
            }]
        }]
        errors = validators.validate_question_groups(data)
        assert errors == [{'name': ['This field is required.'],
                           'questions': [
                                {'name': ['This field is required.']}
                            ]}
                          ]

    def test_valid_nested_questiongroup(self):
        data = [{
            'name': "location_attributes",
            'label': "Location Attributes",
            'type': 'repeat',
            'index': 0,
            'question_groups': [{
                'name': "location_attributes",
                'label': "Location Attributes",
                'type': 'group',
                'index': 0,
            }],
            'questions': [{
                'name': "start",
                'label': 'Start',
                'type': "ST",
                'index': 0,
            }]
        }]
        errors = validators.validate_question_groups(data)
        assert errors == [{}]

    def test_invalid_nested_questiongroup(self):
        data = [{
            'label': "Location Attributes",
            'type': 'repeat',
            'index': 0,
            'question_groups': [{
                'name': "location_attributes",
                'label': "Location Attributes",
                'index': 0
            }],
            'questions': [{
                'label': 'Start',
                'type': "ST",
                'index': 0
            }]
        }]
        errors = validators.validate_question_groups(data)
        assert errors == [{'name': ['This field is required.'],
                           'questions': [
                                {'name': ['This field is required.']}],
                          'question_groups': [
                                {'type': ['This field is required.']}]
                           }
                          ]


class QuestionTestCase(TestCase):
    def test_valid_question(self):
        data = [{
            'name': "start",
            'label': None,
            'type': "ST",
            'required': False,
            'constraint': None,
            'index': 0,
            'gps_accuracy': -1.5
        }]
        errors = validators.validate_questions(data)
        assert errors == [{}]

    def test_invalid_question(self):
        data = [{
            'name': "start",
            'label': None,
            'type': "ST",
            'required': False,
            'constraint': None,
            'index': 0
        }, {
            'label': None,
            'type': "S1",
            'required': False,
            'constraint': None,
            'options': [{'name': 'Name', 'index': 0}],
            'index': 1
        }, {
            'name': 'geom',
            'label': 'geom',
            'type': "GP",
            'required': False,
            'index': 1,
            'gps_accuracy': -1.5
        }]
        errors = validators.validate_questions(data)
        assert errors == [
            {},
            {'name': ['This field is required.'],
             'options': [{'label': ['This field is required.']}]},
            {'gps_accuracy': ['gps_accuracy must be positve float']}
        ]


class QuestionOptionTestCase(TestCase):
    def test_valid_option(self):
        data = [{
            'name': "start",
            'label': "Start",
            'index': 0
        }]
        errors = validators.validate_question_options(data)
        assert errors == [{}]

    def test_invalid_option(self):
        data = [{
            'name': "start",
            'label': "Start",
            'index': 0
        }, {
            'name': "end",
            'index': 1
        }]
        errors = validators.validate_question_options(data)
        assert errors == [{}, {'label': ['This field is required.']}]
