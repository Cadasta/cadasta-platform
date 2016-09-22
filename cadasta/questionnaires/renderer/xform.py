from pyxform.builder import create_survey_element_from_dict
from lxml import etree
from rest_framework.renderers import BaseRenderer
from ..models import Question
from ..managers import fix_languages

QUESTION_TYPES = dict(Question.TYPE_CHOICES)


class XFormRenderer(BaseRenderer):
    format = 'xform'
    media_type = 'application/xml'

    def transform_questions(self, questions):
        children = []
        for q in questions:
            q['type'] = QUESTION_TYPES[q['type']]

            if q.get('label', -1) is None:
                del q['label']

            if 'options' in q:
                q['choices'] = q['options']

            bind = {}
            if q.get('required', False) is True:
                bind['required'] = 'yes'
            if q.get('relevant'):
                bind['relevant'] = q.get('relevant')

            if bind:
                q['bind'] = bind

            children.append(q)
        return children

    def transform_groups(self, groups):
        transformed_groups = []
        for g in groups:
            group = {
                'type': 'group',
                'name': g.get('name'),
                'label': g.get('label'),
                'children': self.transform_questions(g.get('questions'))
            }
            if group['label'] is None:
                del group['label']

            bind = {}
            if g.get('relevant'):
                bind['relevant'] = g.get('relevant')

            if bind:
                group['bind'] = bind
            transformed_groups.append(group)
        return transformed_groups

    def transform_to_xform_json(self, data):
        json = {
            'default_language': 'default',
            'name': data.get('id_string'),
            'sms_keyword': data.get('id_string'),
            'type': 'survey',
            'id_string': data.get('id_string'),
            'title': data.get('id_string')
        }

        questions = self.transform_questions(data.get('questions', []))
        question_groups = self.transform_groups(
            data.get('question_groups', []))
        json['children'] = questions + question_groups
        return json

    def insert_version_attribute(self, xform, root_node, version):
        ns = {'xf': 'http://www.w3.org/2002/xforms'}
        root = etree.fromstring(xform)
        inst = root.find(
            './/xf:instance/xf:{root_node}'.format(
                root_node=root_node
            ), namespaces=ns
        )
        inst.set('version', str(version))
        xml = etree.tostring(
            root, method='xml', encoding='utf-8', pretty_print=True
        )
        return xml

    def render(self, data, *args, **kwargs):
        json = self.transform_to_xform_json(data)
        survey = create_survey_element_from_dict(json)
        xml = survey.xml()
        fix_languages(xml)
        xml = xml.toxml()

        xml = self.insert_version_attribute(xml,
                                            data.get('id_string'),
                                            data.get('version'))

        return xml
