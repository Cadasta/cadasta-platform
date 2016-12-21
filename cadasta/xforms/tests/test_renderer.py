from django.test import TestCase
from ..renderers import XFormRenderer


class XFormRendererTest(TestCase):
    def test_transform_questions(self):
        questions = [{
            'id': "xp8vjr6dsk46p47u22fft7bg",
            'name': "tenure_type",
            'label': "What is the social tenure type?",
            'type': "S1",
            'required': True,
            'constraint': None,
            'default': 'some default',
            'hint': 'An informative hint',
            'relevant': '${party_id}="abc123"',
            'options': [{
                'id': "d9pkepyjg4sgaepdytgwkgfv",
                'name': "WR",
                'label': "Water Rights"
            }, {
                'id': "vz9533y64f2rns6v8frssc5v",
                'name': "UC",
                'label': "Undivided Co-ownership"
            }]
        }, {
            'id': "bzs2984c3gxgwcjhvambdt3w",
            'name': "start",
            'label': None,
            'type': "ST",
            'required': False,
            'constraint': None
        }]
        renderer = XFormRenderer()
        transformed = renderer.transform_questions(questions)
        assert len(transformed) == 2
        for q in transformed:
            if q['name'] == 'start':
                assert q['type'] == 'start'
                assert 'label' not in q
            elif q['name'] == 'tenure_type':
                assert q['type'] == 'select one'
                assert q['choices'] == questions[0]['options']
                assert q['bind']['required'] == 'yes'
                assert q['bind']['relevant'] == '${party_id}="abc123"'
                assert q['default'] == 'some default'
                assert q['hint'] == 'An informative hint'

    def test_transform_groups(self):
        groups = [{
            'id': '123',
            'name': 'group_1',
            'label': 'Group 1',
            'type': 'group',
            'relevant': "${party_type}='IN'",
            'index': 0,
            'questions': [{
                'id': "bzs2984c3gxgwcjhvambdt3w",
                'name': "start",
                'label': None,
                'type': "ST",
                'index': 0
            }]
        }, {
            'id': '456',
            'name': 'group_2',
            'label': None,
            'type': 'repeat',
            'index': 1,
            'questions': [{
                'id': "xp8vjr6dsk46p47u22fft7bg",
                'name': "tenure_type",
                'label': "What is the social tenure type?",
                'type': "TX",
                'index': 0
            }],
            'question_groups': [{
                'id': "xp8vjr6dsk46p47u22fft7aa",
                'name': 'group_3',
                'label': 'Group 3',
                'type': 'group',
                'index': 1
            }]
        }]
        renderer = XFormRenderer()
        transformed = renderer.transform_groups(groups)
        assert len(transformed) == 2
        for g in transformed:
            if g['name'] == 'group_1':
                assert g['bind']['relevant'] == "${party_type}='IN'"
                assert g['type'] == 'group'
                assert len(g['children']) == 1
            if g['name'] == 'group_2':
                assert 'label' not in g
                assert g['type'] == 'repeat'
                assert len(g['children']) == 2

    def test_transform_to_xform_json(self):
        data = {
            'id_string': 'abc123',
            'version': '1234567890',
            'filename': 'abc123',
            'questions': [
                {
                  'id': "xp8vjr6dsk46p47u22fft7bg",
                  'name': "tenure_type",
                  'label': "What is the social tenure type?",
                  'type': "S1",
                  'required': False,
                  'constraint': None,
                  'index': 0,
                  'options': [
                    {
                      'id': "d9pkepyjg4sgaepdytgwkgfv",
                      'name': "WR",
                      'label': "Water Rights"
                    },
                    {
                      'id': "vz9533y64f2rns6v8frssc5v",
                      'name': "UC",
                      'label': "Undivided Co-ownership"
                    },
                  ]
                }
            ],
            'question_groups': [{
                'id': '123',
                'name': 'group_1',
                'label': 'Group 2',
                'index': 1,
                'questions': [{
                    'id': "bzs2984c3gxgwcjhvambdt3w",
                    'name': "start",
                    'label': None,
                    'type': "ST",
                    'index': 0,
                }]
            }, {
                'id': '456',
                'name': 'group_2',
                'label': 'Group 2',
                'index': 2,
                'questions': [{
                    'id': "xp8vjr6dsk46p47u22fft7bg",
                    'name': "party_type",
                    'label': "What is the party type?",
                    'type': "TX",
                    'index': 0,
                }]
            }]
        }
        renderer = XFormRenderer()
        transformed = renderer.transform_to_xform_json(data)
        assert transformed['name'] == 'abc123'
        assert transformed['sms_keyword'] == 'abc123'
        assert transformed['id_string'] == 'abc123'
        assert transformed['title'] == 'abc123'
        assert len(transformed['children']) == 3

    def test_render(self):
        data = {
            'id_string': 'abc123',
            'version': '1234567890',
            'filename': 'abc123',
            'questions': [
                {
                  'id': "xp8vjr6dsk46p47u22fft7bg",
                  'name': "tenure_type",
                  'label': "What is the social tenure type?",
                  'type': "S1",
                  'required': False,
                  'constraint': None,
                  'index': 0,
                  'options': [
                    {
                      'id': "d9pkepyjg4sgaepdytgwkgfv",
                      'name': "WR",
                      'label': "Water Rights"
                    },
                    {
                      'id': "vz9533y64f2rns6v8frssc5v",
                      'name': "UC",
                      'label': "Undivided Co-ownership"
                    },
                  ]
                },
                {
                  'id': "bzs2984c3gxgwcjhvambdt3w",
                  'name': "start",
                  'label': None,
                  'type': "ST",
                  'required': False,
                  'constraint': None,
                  'index': 1,
                }
            ]
        }
        renderer = XFormRenderer()
        xml = renderer.render(data).decode()
        assert '<h:title>abc123</h:title>' in xml
        assert '<abc123 id="abc123" version="1234567890">' in xml
        assert ('<bind calculate="concat(\'uuid:\', uuid())" '
                'nodeset="/abc123/meta/instanceID" readonly="true()" '
                'type="string"/>' in xml)
