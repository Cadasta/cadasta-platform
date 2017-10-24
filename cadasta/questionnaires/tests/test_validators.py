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


class ValidateRelevantTest(TestCase):
    def test_compare_text(self):
        assert validators.validate_relevant("${party_type}='IN'") is True
        assert validators.validate_relevant("${party_type}=\"IN\"") is True
        assert validators.validate_relevant("${party_type}=“IN”") is True
        assert validators.validate_relevant("${party_type}=‘IN’") is True
        assert validators.validate_relevant("${party_type}>'IN'") is True
        assert validators.validate_relevant("${party_type}>\"IN\"") is True
        assert validators.validate_relevant("${party_type}>“IN”") is True
        assert validators.validate_relevant("${party_type}>‘IN’") is True
        assert validators.validate_relevant("${party_type}>='IN'") is True
        assert validators.validate_relevant("${party_type}>=\"IN\"") is True
        assert validators.validate_relevant("${party_type}>=“IN”") is True
        assert validators.validate_relevant("${party_type}>=‘IN’") is True
        assert validators.validate_relevant("${party_type}<'IN'") is True
        assert validators.validate_relevant("${party_type}<\"IN\"") is True
        assert validators.validate_relevant("${party_type}<“IN”") is True
        assert validators.validate_relevant("${party_type}<‘IN’") is True
        assert validators.validate_relevant("${party_type}<='IN'") is True
        assert validators.validate_relevant("${party_type}<=\"IN\"") is True
        assert validators.validate_relevant("${party_type}<=“IN”") is True
        assert validators.validate_relevant("${party_type}<=‘IN’") is True
        assert validators.validate_relevant("${party_type}!='IN'") is True
        assert validators.validate_relevant("${party_type}!=\"IN\"") is True
        assert validators.validate_relevant("${party_type}!=“IN”") is True
        assert validators.validate_relevant("${party_type}!=‘IN’") is True

    def test_compare_numbers(self):
        assert validators.validate_relevant("${party_type}=9") is True
        assert validators.validate_relevant("${party_type}=9") is True
        assert validators.validate_relevant("${party_type}=9") is True
        assert validators.validate_relevant("${party_type}=9") is True
        assert validators.validate_relevant("${party_type}>9") is True
        assert validators.validate_relevant("${party_type}>9") is True
        assert validators.validate_relevant("${party_type}>9") is True
        assert validators.validate_relevant("${party_type}>9") is True
        assert validators.validate_relevant("${party_type}>=9") is True
        assert validators.validate_relevant("${party_type}>=9") is True
        assert validators.validate_relevant("${party_type}>=9") is True
        assert validators.validate_relevant("${party_type}>=9") is True
        assert validators.validate_relevant("${party_type}<9") is True
        assert validators.validate_relevant("${party_type}<9") is True
        assert validators.validate_relevant("${party_type}<9") is True
        assert validators.validate_relevant("${party_type}<9") is True
        assert validators.validate_relevant("${party_type}<=9") is True
        assert validators.validate_relevant("${party_type}<=9") is True
        assert validators.validate_relevant("${party_type}<=9") is True
        assert validators.validate_relevant("${party_type}<=9") is True
        assert validators.validate_relevant("${party_type}!=9") is True
        assert validators.validate_relevant("${party_type}!=9") is True
        assert validators.validate_relevant("${party_type}!=9") is True
        assert validators.validate_relevant("${party_type}!=9") is True

        assert validators.validate_relevant("${party_type}=482") is True
        assert validators.validate_relevant("${party_type}=482") is True
        assert validators.validate_relevant("${party_type}=482") is True
        assert validators.validate_relevant("${party_type}=482") is True
        assert validators.validate_relevant("${party_type}>482") is True
        assert validators.validate_relevant("${party_type}>482") is True
        assert validators.validate_relevant("${party_type}>482") is True
        assert validators.validate_relevant("${party_type}>482") is True
        assert validators.validate_relevant("${party_type}>=482") is True
        assert validators.validate_relevant("${party_type}>=482") is True
        assert validators.validate_relevant("${party_type}>=482") is True
        assert validators.validate_relevant("${party_type}>=482") is True
        assert validators.validate_relevant("${party_type}<482") is True
        assert validators.validate_relevant("${party_type}<482") is True
        assert validators.validate_relevant("${party_type}<482") is True
        assert validators.validate_relevant("${party_type}<482") is True
        assert validators.validate_relevant("${party_type}<=482") is True
        assert validators.validate_relevant("${party_type}<=482") is True
        assert validators.validate_relevant("${party_type}<=482") is True
        assert validators.validate_relevant("${party_type}<=482") is True
        assert validators.validate_relevant("${party_type}!=482") is True
        assert validators.validate_relevant("${party_type}!=482") is True
        assert validators.validate_relevant("${party_type}!=482") is True
        assert validators.validate_relevant("${party_type}!=482") is True

    def test_selected(self):
        assert validators.validate_relevant(
            "selected(${assets}, ‘nets’)") is True
        assert validators.validate_relevant(
            "selected(${assets}, 'nets')") is True
        assert validators.validate_relevant(
            "selected(${assets}, \"nets\")") is True
        assert validators.validate_relevant(
            "selected(${assets}, “nets”)") is True

    def test_not_text(self):
        assert validators.validate_relevant("not(${party_type}='IN')") is True
        assert validators.validate_relevant(
            "not(${party_type}=\"IN\")") is True
        assert validators.validate_relevant("not(${party_type}=“IN”)") is True
        assert validators.validate_relevant("not(${party_type}=‘IN’)") is True
        assert validators.validate_relevant("not(${party_type}>'IN')") is True
        assert validators.validate_relevant(
            "not(${party_type}>\"IN\")") is True
        assert validators.validate_relevant("not(${party_type}>“IN”)") is True
        assert validators.validate_relevant("not(${party_type}>‘IN’)") is True
        assert validators.validate_relevant("not(${party_type}>='IN')") is True
        assert validators.validate_relevant(
            "not(${party_type}>=\"IN\")") is True
        assert validators.validate_relevant("not(${party_type}>=“IN”)") is True
        assert validators.validate_relevant("not(${party_type}>=‘IN’)") is True
        assert validators.validate_relevant("not(${party_type}<'IN')") is True
        assert validators.validate_relevant(
            "not(${party_type}<\"IN\")") is True
        assert validators.validate_relevant("not(${party_type}<“IN”)") is True
        assert validators.validate_relevant("not(${party_type}<‘IN’)") is True
        assert validators.validate_relevant("not(${party_type}<='IN')") is True
        assert validators.validate_relevant(
            "not(${party_type}<=\"IN\")") is True
        assert validators.validate_relevant("not(${party_type}<=“IN”)") is True
        assert validators.validate_relevant("not(${party_type}<=‘IN’)") is True
        assert validators.validate_relevant("not(${party_type}!='IN')") is True
        assert validators.validate_relevant(
            "not(${party_type}!=\"IN\")") is True
        assert validators.validate_relevant("not(${party_type}!=“IN”)") is True
        assert validators.validate_relevant("not(${party_type}!=‘IN’)") is True

    def test_not_number(self):
        assert validators.validate_relevant("not(${party_type}=9)") is True
        assert validators.validate_relevant("not(${party_type}=9)") is True
        assert validators.validate_relevant("not(${party_type}=9)") is True
        assert validators.validate_relevant("not(${party_type}=9)") is True
        assert validators.validate_relevant("not(${party_type}>9)") is True
        assert validators.validate_relevant("not(${party_type}>9)") is True
        assert validators.validate_relevant("not(${party_type}>9)") is True
        assert validators.validate_relevant("not(${party_type}>9)") is True
        assert validators.validate_relevant("not(${party_type}>=9)") is True
        assert validators.validate_relevant("not(${party_type}>=9)") is True
        assert validators.validate_relevant("not(${party_type}>=9)") is True
        assert validators.validate_relevant("not(${party_type}>=9)") is True
        assert validators.validate_relevant("not(${party_type}<9)") is True
        assert validators.validate_relevant("not(${party_type}<9)") is True
        assert validators.validate_relevant("not(${party_type}<9)") is True
        assert validators.validate_relevant("not(${party_type}<9)") is True
        assert validators.validate_relevant("not(${party_type}<=9)") is True
        assert validators.validate_relevant("not(${party_type}<=9)") is True
        assert validators.validate_relevant("not(${party_type}<=9)") is True
        assert validators.validate_relevant("not(${party_type}<=9)") is True
        assert validators.validate_relevant("not(${party_type}!=9)") is True
        assert validators.validate_relevant("not(${party_type}!=9)") is True
        assert validators.validate_relevant("not(${party_type}!=9)") is True
        assert validators.validate_relevant("not(${party_type}!=9)") is True

        assert validators.validate_relevant("not(${party_type}=482)") is True
        assert validators.validate_relevant("not(${party_type}=482)") is True
        assert validators.validate_relevant("not(${party_type}=482)") is True
        assert validators.validate_relevant("not(${party_type}=482)") is True
        assert validators.validate_relevant("not(${party_type}>482)") is True
        assert validators.validate_relevant("not(${party_type}>482)") is True
        assert validators.validate_relevant("not(${party_type}>482)") is True
        assert validators.validate_relevant("not(${party_type}>482)") is True
        assert validators.validate_relevant("not(${party_type}>=482)") is True
        assert validators.validate_relevant("not(${party_type}>=482)") is True
        assert validators.validate_relevant("not(${party_type}>=482)") is True
        assert validators.validate_relevant("not(${party_type}>=482)") is True
        assert validators.validate_relevant("not(${party_type}<482)") is True
        assert validators.validate_relevant("not(${party_type}<482)") is True
        assert validators.validate_relevant("not(${party_type}<482)") is True
        assert validators.validate_relevant("not(${party_type}<482)") is True
        assert validators.validate_relevant("not(${party_type}<=482)") is True
        assert validators.validate_relevant("not(${party_type}<=482)") is True
        assert validators.validate_relevant("not(${party_type}<=482)") is True
        assert validators.validate_relevant("not(${party_type}<=482)") is True
        assert validators.validate_relevant("not(${party_type}!=482)") is True
        assert validators.validate_relevant("not(${party_type}!=482)") is True
        assert validators.validate_relevant("not(${party_type}!=482)") is True
        assert validators.validate_relevant("not(${party_type}!=482)") is True

    def test_not_selected(self):
        assert validators.validate_relevant(
            "not(selected(${assets}, ‘nets’))") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, 'nets'))") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, \"nets\"))") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, “nets”))") is True

    def test_logic(self):
        assert validators.validate_relevant(
            "selected(${assets}, ‘nets’) and ${party_type}='IN'") is True
        assert validators.validate_relevant(
            "selected(${assets}, 'nets') and ${party_type}=\"IN\"") is True
        assert validators.validate_relevant(
            "selected(${assets}, \"nets\") and ${party_type}=“IN”") is True
        assert validators.validate_relevant(
            "selected(${assets}, “nets”) and ${party_type}=‘IN’") is True
        assert validators.validate_relevant(
            "${party_type}='IN' and selected(${assets}, ‘nets’)") is True
        assert validators.validate_relevant(
            "${party_type}=\"IN\" and selected(${assets}, 'nets')") is True
        assert validators.validate_relevant(
            "${party_type}=“IN” and selected(${assets}, \"nets\")") is True
        assert validators.validate_relevant(
            "${party_type}=‘IN’ and selected(${assets}, “nets”)") is True

        assert validators.validate_relevant(
            "selected(${assets}, ‘nets’) or ${party_type}='IN'") is True
        assert validators.validate_relevant(
            "selected(${assets}, 'nets') or ${party_type}=\"IN\"") is True
        assert validators.validate_relevant(
            "selected(${assets}, \"nets\") or ${party_type}=“IN”") is True
        assert validators.validate_relevant(
            "selected(${assets}, “nets”) or ${party_type}=‘IN’") is True
        assert validators.validate_relevant(
            "${party_type}='IN' or selected(${assets}, ‘nets’)") is True
        assert validators.validate_relevant(
            "${party_type}=\"IN\" or selected(${assets}, 'nets')") is True
        assert validators.validate_relevant(
            "${party_type}=“IN” or selected(${assets}, \"nets\")") is True
        assert validators.validate_relevant(
            "${party_type}=‘IN’ or selected(${assets}, “nets”)") is True

    def test_not_logic(self):
        assert validators.validate_relevant(
            "not(selected(${assets}, ‘nets’)) and ${party_type}='IN'") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, 'nets')) "
            "and ${party_type}=\"IN\"") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, \"nets\")) "
            "and ${party_type}=“IN”") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, “nets”)) and ${party_type}=‘IN’") is True
        assert validators.validate_relevant(
            "not(${party_type}='IN') and selected(${assets}, ‘nets’)") is True
        assert validators.validate_relevant(
            "not(${party_type}=\"IN\") and "
            "selected(${assets}, 'nets')") is True
        assert validators.validate_relevant(
            "not(${party_type}=“IN”) and "
            "selected(${assets}, \"nets\")") is True
        assert validators.validate_relevant(
            "not(${party_type}=‘IN’) and selected(${assets}, “nets”)") is True

        assert validators.validate_relevant(
            "not(selected(${assets}, ‘nets’)) or ${party_type}='IN'") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, 'nets')) or ${party_type}=\"IN\"") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, \"nets\")) or ${party_type}=“IN”") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, “nets”)) or ${party_type}=‘IN’") is True
        assert validators.validate_relevant(
            "not(${party_type}='IN') or selected(${assets}, ‘nets’)") is True
        assert validators.validate_relevant(
            "not(${party_type}=\"IN\") or selected(${assets}, 'nets')") is True
        assert validators.validate_relevant(
            "not(${party_type}=“IN”) or selected(${assets}, \"nets\")") is True
        assert validators.validate_relevant(
            "not(${party_type}=‘IN’) or selected(${assets}, “nets”)") is True

        assert validators.validate_relevant(
            "selected(${assets}, ‘nets’) and not(${party_type}='IN')") is True
        assert validators.validate_relevant(
            "selected(${assets}, 'nets') and "
            "not(${party_type}=\"IN\")") is True
        assert validators.validate_relevant(
            "selected(${assets}, \"nets\") and "
            "not(${party_type}=“IN”)") is True
        assert validators.validate_relevant(
            "selected(${assets}, “nets”) and not(${party_type}=‘IN’)") is True
        assert validators.validate_relevant(
            "${party_type}='IN' and not(selected(${assets}, ‘nets’))") is True
        assert validators.validate_relevant(
            "${party_type}=\"IN\" and "
            "not(selected(${assets}, 'nets'))") is True
        assert validators.validate_relevant(
            "${party_type}=“IN” and "
            "not(selected(${assets}, \"nets\"))") is True
        assert validators.validate_relevant(
            "${party_type}=‘IN’ and not(selected(${assets}, “nets”))") is True

        assert validators.validate_relevant(
            "selected(${assets}, ‘nets’) or not(${party_type}='IN')") is True
        assert validators.validate_relevant(
            "selected(${assets}, 'nets') or not(${party_type}=\"IN\")") is True
        assert validators.validate_relevant(
            "selected(${assets}, \"nets\") or not(${party_type}=“IN”)") is True
        assert validators.validate_relevant(
            "selected(${assets}, “nets”) or not(${party_type}=‘IN’)") is True
        assert validators.validate_relevant(
            "${party_type}='IN' or not(selected(${assets}, ‘nets’))") is True
        assert validators.validate_relevant(
            "${party_type}=\"IN\" or not(selected(${assets}, 'nets'))") is True
        assert validators.validate_relevant(
            "${party_type}=“IN” or not(selected(${assets}, \"nets\"))") is True
        assert validators.validate_relevant(
            "${party_type}=‘IN’ or not(selected(${assets}, “nets”))") is True

        assert validators.validate_relevant(
            "not(selected(${assets}, ‘nets’)) and "
            "not(${party_type}='IN')") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, 'nets')) and "
            "not(${party_type}=\"IN\")") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, \"nets\")) and "
            "not(${party_type}=“IN”)") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, “nets”)) and "
            "not(${party_type}=‘IN’)") is True
        assert validators.validate_relevant(
            "not(${party_type}='IN') and "
            "not(selected(${assets}, ‘nets’))") is True
        assert validators.validate_relevant(
            "not(${party_type}=\"IN\") and "
            "not(selected(${assets}, 'nets'))") is True
        assert validators.validate_relevant(
            "not(${party_type}=“IN”) and "
            "not(selected(${assets}, \"nets\"))") is True
        assert validators.validate_relevant(
            "not(${party_type}=‘IN’) and "
            "not(selected(${assets}, “nets”))") is True

        assert validators.validate_relevant(
            "not(selected(${assets}, ‘nets’)) or "
            "not(${party_type}='IN')") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, 'nets')) or "
            "not(${party_type}=\"IN\")") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, \"nets\")) or "
            "not(${party_type}=“IN”)") is True
        assert validators.validate_relevant(
            "not(selected(${assets}, “nets”)) or "
            "not(${party_type}=‘IN’)") is True
        assert validators.validate_relevant(
            "not(${party_type}='IN') or "
            "not(selected(${assets}, ‘nets’))") is True
        assert validators.validate_relevant(
            "not(${party_type}=\"IN\") or "
            "not(selected(${assets}, 'nets'))") is True
        assert validators.validate_relevant(
            "not(${party_type}=“IN”) or "
            "not(selected(${assets}, \"nets\"))") is True
        assert validators.validate_relevant(
            "not(${party_type}=‘IN’) or "
            "not(selected(${assets}, “nets”))") is True

    def test_invalid_compare_text(self):
        assert validators.validate_relevant("$party_type=”IN”") is False
        assert validators.validate_relevant("${party_type}=”IN”") is False
        assert validators.validate_relevant("${party_type}=’IN‘") is False
        assert validators.validate_relevant("${party_type}=>'IN'") is False
        assert validators.validate_relevant("${party_type}=>\"IN\"") is False
        assert validators.validate_relevant("${party_type}=>”IN”") is False
        assert validators.validate_relevant("${party_type}=>‘IN’") is False
        assert validators.validate_relevant("${party_type}=<'IN'") is False
        assert validators.validate_relevant("${party_type}=<\"IN\"") is False
        assert validators.validate_relevant("${party_type}=<”IN”") is False
        assert validators.validate_relevant("${party_type}=<‘IN’") is False
        assert validators.validate_relevant("${party_type}=!'IN'") is False
        assert validators.validate_relevant("${party_type}=!\"IN\"") is False
        assert validators.validate_relevant("${party_type}=!”IN”") is False
        assert validators.validate_relevant("${party_type}=!‘IN’") is False

    def test_invalid_compare_number(self):
        assert validators.validate_relevant("${party_type}=>9") is False
        assert validators.validate_relevant("${party_type}=>9") is False
        assert validators.validate_relevant("${party_type}=>9") is False
        assert validators.validate_relevant("${party_type}=>9") is False
        assert validators.validate_relevant("${party_type}=<9") is False
        assert validators.validate_relevant("${party_type}=<9") is False
        assert validators.validate_relevant("${party_type}=<9") is False
        assert validators.validate_relevant("${party_type}=<9") is False
        assert validators.validate_relevant("${party_type}=!9") is False
        assert validators.validate_relevant("${party_type}=!9") is False
        assert validators.validate_relevant("${party_type}=!9") is False
        assert validators.validate_relevant("${party_type}=!9") is False

        assert validators.validate_relevant("${party_type}=>482") is False
        assert validators.validate_relevant("${party_type}=>482") is False
        assert validators.validate_relevant("${party_type}=>482") is False
        assert validators.validate_relevant("${party_type}=>482") is False
        assert validators.validate_relevant("${party_type}=<482") is False
        assert validators.validate_relevant("${party_type}=<482") is False
        assert validators.validate_relevant("${party_type}=<482") is False
        assert validators.validate_relevant("${party_type}=<482") is False
        assert validators.validate_relevant("${party_type}=!482") is False
        assert validators.validate_relevant("${party_type}=!482") is False
        assert validators.validate_relevant("${party_type}=!482") is False
        assert validators.validate_relevant("${party_type}=!482") is False

    def test_invalid_selected(self):
        assert validators.validate_relevant(
            "selected($assets, ’nets‘)") is False
        assert validators.validate_relevant(
            "selected(${assets}, ’nets‘)") is False
        assert validators.validate_relevant(
            "selected(${assets}, ”nets”)") is False
        assert validators.validate_relevant(
            "selected(${assets}, 'nets'") is False
        assert validators.validate_relevant(
            "selected${assets}, 'nets')") is False
        assert validators.validate_relevant(
            "selected${assets}, 'nets'") is False
        assert validators.validate_relevant(
            "selected ${assets}, 'nets')") is False
        assert validators.validate_relevant(
            "selected ${assets}, 'nets'") is False

    def test_invalid_not_text(self):
        assert validators.validate_relevant(
            "not(${party_type}=”IN”)") is False
        assert validators.validate_relevant(
            "not(${party_type}=’IN‘)") is False
        assert validators.validate_relevant(
            "not(${party_type}=>'IN')") is False
        assert validators.validate_relevant(
            "not(${party_type}=>\"IN\")") is False
        assert validators.validate_relevant(
            "not(${party_type}=>”IN”)") is False
        assert validators.validate_relevant(
            "not(${party_type}=>‘IN’)") is False
        assert validators.validate_relevant(
            "not(${party_type}=<'IN')") is False
        assert validators.validate_relevant(
            "not(${party_type}=<\"IN\")") is False
        assert validators.validate_relevant(
            "not(${party_type}=<”IN”)") is False
        assert validators.validate_relevant(
            "not(${party_type}=<‘IN’)") is False
        assert validators.validate_relevant(
            "not(${party_type}=!'IN')") is False
        assert validators.validate_relevant(
            "not(${party_type}=!\"IN\")") is False
        assert validators.validate_relevant(
            "not(${party_type}=!”IN”)") is False
        assert validators.validate_relevant(
            "not(${party_type}=!‘IN’)") is False

    def test_invalid_not_number(self):
        assert validators.validate_relevant("not(${party_type}=>9)") is False
        assert validators.validate_relevant("not(${party_type}=>9)") is False
        assert validators.validate_relevant("not(${party_type}=>9)") is False
        assert validators.validate_relevant("not(${party_type}=>9)") is False
        assert validators.validate_relevant("not(${party_type}=<9)") is False
        assert validators.validate_relevant("not(${party_type}=<9)") is False
        assert validators.validate_relevant("not(${party_type}=<9)") is False
        assert validators.validate_relevant("not(${party_type}=<9)") is False
        assert validators.validate_relevant("not(${party_type}=!9)") is False
        assert validators.validate_relevant("not(${party_type}=!9)") is False
        assert validators.validate_relevant("not(${party_type}=!9)") is False
        assert validators.validate_relevant("not(${party_type}=!9)") is False

        assert validators.validate_relevant("not(${party_type}=>482)") is False
        assert validators.validate_relevant("not(${party_type}=>482)") is False
        assert validators.validate_relevant("not(${party_type}=>482)") is False
        assert validators.validate_relevant("not(${party_type}=>482)") is False
        assert validators.validate_relevant("not(${party_type}=<482)") is False
        assert validators.validate_relevant("not(${party_type}=<482)") is False
        assert validators.validate_relevant("not(${party_type}=<482)") is False
        assert validators.validate_relevant("not(${party_type}=<482)") is False
        assert validators.validate_relevant("not(${party_type}=!482)") is False
        assert validators.validate_relevant("not(${party_type}=!482)") is False
        assert validators.validate_relevant("not(${party_type}=!482)") is False
        assert validators.validate_relevant("not(${party_type}=!482)") is False

        assert validators.validate_relevant("not(${party_type}='IN'") is False
        assert validators.validate_relevant("not(${party_type}='IN' ") is False
        assert validators.validate_relevant("not${party_type}='IN')") is False
        assert validators.validate_relevant("not ${party_type}='IN')") is False

    def test_invalid_not_selected(self):
        assert validators.validate_relevant(
            "not(selected(${assets}, ’nets‘))") is False
        assert validators.validate_relevant(
            "not(selected(${assets}, ”nets”))") is False
        assert validators.validate_relevant(
            "notselected(${assets}, 'nets'))") is False
        assert validators.validate_relevant(
            "not selected(${assets}, 'nets'))") is False
        assert validators.validate_relevant(
            "not(selected(${assets}, 'nets')") is False
        assert validators.validate_relevant(
            "notselected(${assets}, 'nets')") is False
        assert validators.validate_relevant(
            "not selected(${assets}, 'nets')") is False

    def test_invalid_logic(self):
        assert validators.validate_relevant(
            "not(selected(${assets}, ’nets‘))") is False
        assert validators.validate_relevant(
            "not(selected(${assets}, ”nets”))") is False
        assert validators.validate_relevant(
            "not(selected(${assets}, ‘nets’) and ${party_type}='IN'") is False
        assert validators.validate_relevant(
            "not(selected(${assets}, ‘nets’) or ${party_type}='IN'") is False
        assert validators.validate_relevant(
            "selected(${assets}, ‘nets’) and not(${party_type}='IN'") is False
        assert validators.validate_relevant(
            "selected(${assets}, ‘nets’) or not(${party_type}='IN'") is False
        assert validators.validate_relevant(
            "not(selected(${assets}, ‘nets’) and "
            "not(${party_type}='IN'") is False
        assert validators.validate_relevant(
            "not(selected(${assets}, ‘nets’) or "
            "not(${party_type}='IN'") is False

        assert validators.validate_relevant(
            "notselected(${assets}, ‘nets’)) and ${party_type}='IN'") is False
        assert validators.validate_relevant(
            "notselected(${assets}, ‘nets’)) or ${party_type}='IN'") is False
        assert validators.validate_relevant(
            "selected(${assets}, ‘nets’) and not${party_type}='IN')") is False
        assert validators.validate_relevant(
            "selected(${assets}, ‘nets’) or not${party_type}='IN')") is False
        assert validators.validate_relevant(
            "notselected(${assets}, ‘nets’)) and "
            "not${party_type}='IN')") is False
        assert validators.validate_relevant(
            "notselected(${assets}, ‘nets’)) or "
            "not${party_type}='IN')") is False
