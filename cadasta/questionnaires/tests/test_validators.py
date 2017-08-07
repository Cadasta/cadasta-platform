from django.test import TestCase
from core.messages import SANITIZE_ERROR
from .. import validators


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
            'no_code': '<GotCode>'
        }
        errors = validators.validate_schema(self.SCHEMA, data)
        assert 'This field is required.' in errors['title']
        assert 'Value must be of type string.' in errors['id_string']
        assert 'D is not an accepted value.' in errors['some_list']
        assert SANITIZE_ERROR in errors['no_code']


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
            'index': 0
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
        }]
        errors = validators.validate_questions(data)
        assert errors == [{},
                          {'name': ['This field is required.'],
                           'options': [{'label': ['This field is required.']}]}
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
