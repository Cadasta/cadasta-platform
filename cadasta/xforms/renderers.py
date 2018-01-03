from rest_framework import renderers
from django.utils.xmlutils import SimplerXMLGenerator
from django.utils.six.moves import StringIO
from django.utils.encoding import smart_text
from rest_framework.compat import six

from pyxform.builder import create_survey_element_from_dict
from lxml import etree
from rest_framework.renderers import BaseRenderer
from questionnaires.managers import fix_languages
from questionnaires.choices import QUESTION_TYPES

QUESTION_TYPES = dict(QUESTION_TYPES)


class XFormListRenderer(renderers.BaseRenderer):
    """
    Renderer which serializes to XML.
    """

    media_type = 'text/xml'
    format = 'xml'
    charset = 'utf-8'
    root_node = 'xforms'
    element_node = 'xform'
    xmlns = "http://openrosa.org/xforms/xformsList"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders *obj* into serialized XML.
        """
        # if data is None:
        #     return ''
        # elif isinstance(data, six.string_types):
        #     return data

        stream = StringIO()

        xml = SimplerXMLGenerator(stream, self.charset)
        xml.startDocument()
        xml.startElement(self.root_node, {'xmlns': self.xmlns})

        self._to_xml(xml, data)
        xml.endElement(self.root_node)
        xml.endDocument()
        return stream.getvalue()

    def _to_xml(self, xml, data):
        if isinstance(data, (list, tuple)):
            for item in data:
                xml.startElement(self.element_node, {})
                self._to_xml(xml, item)
                xml.endElement(self.element_node)

        elif isinstance(data, dict):
            for key, value in six.iteritems(data):
                xml.startElement(key, {})
                self._to_xml(xml, value)
                xml.endElement(key)

        else:
            xml.characters(smart_text(data))


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

            control = {}

            if q.get('gps_accuracy'):
                control['accuracyThreshold'] = q.get('gps_accuracy')
            if q.get('appearance'):
                control['appearance'] = q.get('appearance')
            if control:
                q['control'] = control

            children.append(q)
        return children

    def transform_groups(self, groups):
        transformed_groups = []
        for g in groups:
            questions = self.transform_questions(g.get('questions', []))
            groups = self.transform_groups(g.get('question_groups', []))
            children = sorted(questions + groups,
                              key=lambda x: x['index'])
            group = {
                'type': g.get('type', 'group'),
                'name': g.get('name'),
                'label': g.get('label'),
                'children': children,
                'index': g.get('index')
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
        json['children'] = sorted(questions + question_groups,
                                  key=lambda x: x['index'])
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

    def insert_uuid_bind(self, xform, id_string):
        ns = {'xf': 'http://www.w3.org/2002/xforms'}
        root = etree.fromstring(xform)
        model = root.find('.//xf:model', namespaces=ns)
        etree.SubElement(model, 'bind', {
            'calculate': "concat('uuid:', uuid())",
            'nodeset': '/{}/meta/instanceID'.format(id_string),
            'readonly': 'true()',
            'type': 'string'
        })
        xml = etree.tostring(
            root, method='xml', encoding='utf-8', pretty_print=True
        )
        return xml

    def render(self, data, *args, **kwargs):
        charset = 'utf-8'
        root_node = 'xforms'
        xmlns = "http://openrosa.org/xforms/xformsList"

        if 'detail' in data.keys():
            stream = StringIO()

            xml = SimplerXMLGenerator(stream, charset)
            xml.startDocument()
            xml.startElement(root_node, {'xmlns': xmlns})

            for key, value in six.iteritems(data):
                xml.startElement(key, {})
                xml.characters(smart_text(value))
                xml.endElement(key)

            xml.endElement(root_node)
            xml.endDocument()
            return stream.getvalue()
        else:
            json = self.transform_to_xform_json(data)
            survey = create_survey_element_from_dict(json)
            xml = survey.xml()
            fix_languages(xml)
            xml = xml.toxml()

            xml = self.insert_version_attribute(xml,
                                                data.get('id_string'),
                                                data.get('version'))
            xml = self.insert_uuid_bind(xml, data.get('id_string'))

            return xml
