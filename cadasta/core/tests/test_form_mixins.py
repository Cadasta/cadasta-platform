from core.tests.utils.cases import FileStorageTestCase, UserTestCase
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from jsonattrs.models import (Attribute, AttributeType, Schema,
                              create_attribute_type)
from organization.tests.factories import ProjectFactory
from party.models import Party
from party.tests.factories import PartyFactory

from ..form_mixins import AttributeForm, AttributeFormMixin, AttributeModelForm
from ..mixins import SchemaSelectorMixin


class MockAttributeForm(AttributeForm):

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        self.add_attribute_fields(content_type)


class MockAttributeModelForm(AttributeModelForm):

    attributes_field = 'attributes'

    class Meta:
        model = Party
        fields = ['name', 'type']

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.add_attribute_fields()


class AttributeFormMixinTest(UserTestCase, FileStorageTestCase, TestCase):

    def setUp(self):
        self.project = ProjectFactory.create(current_questionnaire='abc1')

        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(self.project.organization.id, self.project.id, 'abc1'))
        create_attribute_type('text', 'Text', 'CharField',
                              validator_type='str')
        create_attribute_type('boolean', 'boolean', 'BooleanField',
                              validator_type='bool')
        create_attribute_type('integer', 'Integer', 'IntegerField',
                              validator_re=r'[-+]?\d+')
        Attribute.objects.create(
            schema=schema,
            name='fname',
            long_name='Test field',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema,
            name='homeowner',
            long_name='Homeowner',
            choices=['yes', 'no'],
            default='yes', required=True,
            attr_type=AttributeType.objects.get(name='boolean'),
            index=1
        )
        Attribute.objects.create(
            schema=schema,
            name='number_of_something',
            long_name='Number of something',
            default='0', required=False,
            attr_type=AttributeType.objects.get(name='integer'),
            index=2
        )

    def test_create_model_fields(self):
        form_mixin = AttributeFormMixin()
        schema_mixin = SchemaSelectorMixin()
        form_mixin.fields = {}
        attributes = schema_mixin.get_model_attributes(
            self.project, 'party.party')
        form_mixin.create_model_fields('party', attributes, new_item=False)
        assert len(form_mixin.fields) == 9
        homeowner = form_mixin.fields['party::in::homeowner']
        assert homeowner.initial
        assert homeowner.required

        fname = form_mixin.fields['party::in::fname']
        assert not fname.required
        assert fname.initial is None

        number = form_mixin.fields['party::in::number_of_something']
        assert not number.required
        assert number.initial == '0'

    def test_create_model_fields_with_new_item(self):
        form_mixin = AttributeFormMixin()
        schema_mixin = SchemaSelectorMixin()
        form_mixin.fields = {}
        attributes = schema_mixin.get_model_attributes(
            self.project, 'party.party')
        form_mixin.create_model_fields('party', attributes, new_item=True)
        assert len(form_mixin.fields) == 9

        homeowner = form_mixin.fields['party::in::homeowner']
        assert homeowner.initial
        assert homeowner.required

        fname = form_mixin.fields['party::in::fname']
        assert not fname.required
        assert fname.initial is None

        number = form_mixin.fields['party::in::number_of_something']
        assert not number.required
        assert number.initial == '0'

    def test_process_attributes(self):
        data = {
            'name': 'Cadasta',
            'type': 'IN',
            'party::in::fname': 'test',
            'party::in::number_of_something': '12',
            'party::in::homeowner': True
        }
        form_mixin = AttributeFormMixin()
        schema_mixin = SchemaSelectorMixin()
        form_mixin.fields = {}
        attributes = schema_mixin.get_model_attributes(
            self.project, 'party.party'
        )
        form_mixin.create_model_fields('party', attributes, new_item=False)
        setattr(form_mixin, 'cleaned_data', data)
        processed_attributes = form_mixin.process_attributes(
            'party', entity_type='IN'
        )
        assert processed_attributes['fname'] == 'test'
        assert processed_attributes['homeowner']
        assert processed_attributes['number_of_something'] == '12'


class AttributeFormBaseTest(UserTestCase, FileStorageTestCase, TestCase):

    def setUp(self):
        self.project = ProjectFactory.create(current_questionnaire='abc1')

        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema1 = Schema.objects.create(
            content_type=content_type,
            selectors=(
                self.project.organization.id, self.project.id, 'abc1'))
        schema2 = Schema.objects.create(
            content_type=content_type,
            selectors=(
                self.project.organization.id, self.project.id, 'abc1', 'GR'))
        create_attribute_type('text', 'Text', 'CharField',
                              validator_type='str')
        create_attribute_type('boolean', 'boolean', 'BooleanField',
                              validator_type='bool')
        Attribute.objects.create(
            schema=schema1,
            name='fname',
            long_name='Test field',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema2,
            name='homeowner',
            long_name='Homeowner',
            attr_type=AttributeType.objects.get(name='boolean'),
            index=1
        )


class AttributeFormTest(AttributeFormBaseTest):

    def test_add_attribute_fields(self):
        form = MockAttributeForm(self.project, data={})
        assert len(form.fields) == 4
        attr = form.fields.get('party::gr::homeowner')
        assert attr is not None
        assert attr.label == 'Homeowner'


class AttributeModelFormTest(AttributeFormBaseTest):

    def test_add_attribute_fields(self):
        party = PartyFactory.create()
        form = MockAttributeModelForm(self.project, instance=party)
        assert len(form.fields) == 6
        attr = form.fields.get('party::gr::homeowner')
        assert attr is not None
        assert attr.label == 'Homeowner'
