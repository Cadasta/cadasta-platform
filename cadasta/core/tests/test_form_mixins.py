from core.tests.utils.cases import FileStorageTestCase, UserTestCase
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.forms import CharField, ChoiceField, Form, IntegerField
from jsonattrs.models import (Attribute, AttributeType, Schema,
                              create_attribute_type)
from organization.tests.factories import ProjectFactory
from party.models import Party
from party.tests.factories import PartyFactory
from questionnaires.tests import factories as q_factories

from .. import form_mixins
from ..mixins import SchemaSelectorMixin
from ..widgets import XLangSelect
from ..messages import SANITIZE_ERROR


class MockAttributeForm(form_mixins.AttributeForm):

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        self.add_attribute_fields(content_type)


class MockAttributeModelForm(form_mixins.AttributeModelForm):

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
            selectors=(self.project.organization.id, self.project.id, 'abc1'),
            default_language='en')

        create_attribute_type('text', 'Text', 'CharField',
                              validator_type='str')
        create_attribute_type('boolean', 'boolean', 'BooleanField',
                              validator_type='bool')
        create_attribute_type('integer', 'Integer', 'IntegerField',
                              validator_re=r'[-+]?\d+')
        create_attribute_type('select_one', 'Select one:', 'ChoiceField')
        create_attribute_type('select_multiple', 'Select multiple:',
                              'MultipleChoiceField')
        Attribute.objects.create(
            schema=schema,
            name='fname',
            long_name={'en': 'Test field', 'de': 'Test feld'},
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema,
            name='homeowner',
            long_name={'en': 'Homeowner', 'de': 'Besitzer'},
            choices=['yes', 'no'],
            default='yes', required=True,
            attr_type=AttributeType.objects.get(name='boolean'),
            index=1
        )
        Attribute.objects.create(
            schema=schema,
            name='number_of_something',
            long_name={'en': 'Number of something', 'de': 'Eine Nummer'},
            default='0', required=False,
            attr_type=AttributeType.objects.get(name='integer'),
            index=2
        )
        Attribute.objects.create(
            schema=schema,
            name='bird_is_the_word',
            long_name={'en': 'Have you heard?', 'de': 'Schon gehoert?'},
            choices=['yes', 'no'],
            choice_labels=[{'en': 'yes', 'de': 'ja'},
                           {'en': 'no', 'de': 'nein'}],
            default='yes', required=True,
            attr_type=AttributeType.objects.get(name='select_one'),
            index=3
        )
        Attribute.objects.create(
            schema=schema,
            name='surfing_bird',
            long_name={'en': 'Have you heard?', 'de': 'Schon gehoert?'},
            choices=['yes', 'no'],
            choice_labels=[{'en': 'yes', 'de': 'ja'},
                           {'en': 'no', 'de': 'nein'}],
            default='yes', required=True,
            attr_type=AttributeType.objects.get(name='select_multiple'),
            index=4
        )

    def test_create_model_fields(self):
        form_mixin = form_mixins.AttributeFormMixin()
        schema_mixin = SchemaSelectorMixin()
        form_mixin.fields = {}
        attributes = schema_mixin.get_model_attributes(
            self.project, 'party.party')
        form_mixin.create_model_fields('party', attributes, new_item=False)
        assert len(form_mixin.fields) == 15
        homeowner = form_mixin.fields['party::in::homeowner']
        assert homeowner.initial
        assert homeowner.required

        bird = form_mixin.fields['party::in::bird_is_the_word']
        assert isinstance(bird.widget, XLangSelect)
        assert bird.widget.xlang_labels == {
            'yes': {'en': 'yes', 'de': 'ja'},
            'no': {'en': 'no', 'de': 'nein'}
        }

        surfing_bird = form_mixin.fields['party::in::surfing_bird']
        assert isinstance(surfing_bird.widget, XLangSelect)
        assert surfing_bird.widget.xlang_labels == {
            'yes': {'en': 'yes', 'de': 'ja'},
            'no': {'en': 'no', 'de': 'nein'}
        }

        fname = form_mixin.fields['party::in::fname']
        assert not fname.required
        assert fname.initial is None

        number = form_mixin.fields['party::in::number_of_something']
        assert not number.required
        assert number.initial == '0'

    def test_create_model_fields_with_new_item(self):
        form_mixin = form_mixins.AttributeFormMixin()
        schema_mixin = SchemaSelectorMixin()
        form_mixin.fields = {}
        attributes = schema_mixin.get_model_attributes(
            self.project, 'party.party')
        form_mixin.create_model_fields('party', attributes, new_item=True)

        assert len(form_mixin.fields) == 15

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
        form_mixin = form_mixins.AttributeFormMixin()
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

    def test_set_standard_field(self):
        form_mixin = form_mixins.AttributeFormMixin()
        form_mixin.project = self.project
        form_mixin.fields = {'party_name': CharField()}
        questionnaire = q_factories.QuestionnaireFactory(project=self.project)
        q_factories.QuestionFactory.create(
            name='party_name',
            questionnaire=questionnaire,
            label={'en': 'Name', 'de': 'Name'})
        form_mixin.set_standard_field('party_name')

        assert 'en="Name"' in form_mixin.fields['party_name'].labels_xlang
        assert 'de="Name"' in form_mixin.fields['party_name'].labels_xlang

    def test_set_standard_field_set_field_name(self):
        form_mixin = form_mixins.AttributeFormMixin()
        form_mixin.project = self.project
        form_mixin.fields = {'name': CharField()}
        questionnaire = q_factories.QuestionnaireFactory(project=self.project)
        q_factories.QuestionFactory.create(
            name='party_name',
            questionnaire=questionnaire,
            label={'en': 'Name', 'de': 'Name'})
        form_mixin.set_standard_field('party_name', field_name='name')

        assert 'en="Name"' in form_mixin.fields['name'].labels_xlang
        assert 'de="Name"' in form_mixin.fields['name'].labels_xlang

    def test_set_standard_field_no_question(self):
        form_mixin = form_mixins.AttributeFormMixin()
        form_mixin.project = self.project
        form_mixin.fields = {'name': CharField()}
        questionnaire = q_factories.QuestionnaireFactory(project=self.project)
        q_factories.QuestionFactory.create(
            name='party_name',
            questionnaire=questionnaire,
            label={'en': 'Name', 'de': 'Name'})
        form_mixin.set_standard_field('name',)

        assert hasattr(form_mixin.fields['name'], 'labels_xlang') is False

    def test_set_standard_field_with_options(self):
        form_mixin = form_mixins.AttributeFormMixin()
        form_mixin.project = self.project
        form_mixin.fields = {'building': ChoiceField(
            choices=(('barn', 'Barn'), ('house', 'House')))}
        questionnaire = q_factories.QuestionnaireFactory(
            project=self.project,
            default_language='de')
        question = q_factories.QuestionFactory.create(
            type='S1',
            name='building',
            questionnaire=questionnaire,
            label={'en': 'Name', 'de': 'Name'})
        q_factories.QuestionOptionFactory(
            question=question,
            name='barn',
            label={'de': 'Scheune', 'en': 'Barn'},
            index=0)
        q_factories.QuestionOptionFactory(
            question=question,
            name='house',
            label={'de': 'Haus', 'en': 'Haus'},
            index=1)
        form_mixin.set_standard_field('building')

        widget = form_mixin.fields['building'].widget
        assert isinstance(widget, XLangSelect) is True
        assert widget.choices == [('barn', 'Scheune'), ('house', 'Haus')]
        assert widget.xlang_labels == {
            'barn': {'de': 'Scheune', 'en': 'Barn'},
            'house': {'de': 'Haus', 'en': 'Haus'}
        }

    def test_set_standard_field_with_empty_choice(self):
        form_mixin = form_mixins.AttributeFormMixin()
        form_mixin.project = self.project
        form_mixin.fields = {'building': ChoiceField(
            choices=(('barn', 'Barn'), ('house', 'House')))}
        questionnaire = q_factories.QuestionnaireFactory(
            project=self.project,
            default_language='de')
        question = q_factories.QuestionFactory.create(
            type='S1',
            name='building',
            questionnaire=questionnaire,
            label={'en': 'Name', 'de': 'Name'})
        q_factories.QuestionOptionFactory(
            question=question,
            name='barn',
            label={'de': 'Scheune', 'en': 'Barn'},
            index=0)
        q_factories.QuestionOptionFactory(
            question=question,
            name='house',
            label={'de': 'Haus', 'en': 'Haus'},
            index=1)
        form_mixin.set_standard_field('building',
                                      empty_choice='Select house type')

        widget = form_mixin.fields['building'].widget
        assert isinstance(widget, XLangSelect) is True
        assert widget.choices == [
            ('', 'Select house type'),
            ('barn', 'Scheune'),
            ('house', 'Haus')
        ]
        assert widget.xlang_labels == {
            'barn': {'de': 'Scheune', 'en': 'Barn'},
            'house': {'de': 'Haus', 'en': 'Haus'}
        }

    def test_set_standard_field_with_single_lang(self):
        form_mixin = form_mixins.AttributeFormMixin()
        form_mixin.project = self.project
        form_mixin.fields = {'building': ChoiceField(
            choices=(('barn', 'Barn'), ('house', 'House')))}
        questionnaire = q_factories.QuestionnaireFactory(
            project=self.project)
        question = q_factories.QuestionFactory.create(
            type='S1',
            name='building',
            questionnaire=questionnaire,
            label='Name')
        q_factories.QuestionOptionFactory(
            question=question,
            name='barn',
            label='Barn',
            index=0)
        q_factories.QuestionOptionFactory(
            question=question,
            name='house',
            label='House',
            index=1)
        form_mixin.set_standard_field('building',
                                      empty_choice='Select house type')

        widget = form_mixin.fields['building'].widget
        assert isinstance(widget, XLangSelect) is True
        assert widget.choices == [
            ('', 'Select house type'),
            ('barn', 'Barn'),
            ('house', 'House')
        ]
        assert widget.xlang_labels == {}


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


class MockSanitizeFieldsForm(form_mixins.SanitizeFieldsForm, Form):
    name = CharField()
    number = IntegerField()


class SanitizeFieldsFormTest(TestCase):
    def test_valid_form(self):
        data = {
            'name': 'Name',
            'number': 1
        }
        form = MockSanitizeFieldsForm(data=data)
        assert form.is_valid() is True

    def test_invalid_form_with_code(self):
        data = {
            'name': '<Name>',
            'number': 1
        }
        form = MockSanitizeFieldsForm(data=data)
        assert form.is_valid() is False
        assert SANITIZE_ERROR in form.errors['name']

    def test_invalid_form_with_number(self):
        data = {
            'name': 'Name',
            'number': 'text'
        }
        form = MockSanitizeFieldsForm(data=data)
        assert form.is_valid() is False
        assert form.errors.get('name') is None
        assert form.errors.get('number') is not None

    def test_invalid_form_with_code_and_number(self):
        data = {
            'name': '<Name>',
            'number': 'text'
        }
        form = MockSanitizeFieldsForm(data=data)
        assert form.is_valid() is False
        assert SANITIZE_ERROR in form.errors['name']
        assert form.errors.get('number') is not None
