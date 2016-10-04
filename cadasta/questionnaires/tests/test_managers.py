import os

import pytest
from lxml import etree

from buckets.test.storage import FakeS3Storage
from django.conf import settings
from django.db import IntegrityError
from django.test import TestCase
from django.utils.translation import activate, get_language
from organization.tests.factories import ProjectFactory
from questionnaires.exceptions import InvalidXLSForm
from core.tests.utils.files import make_dirs  # noqa
from core.tests.utils.cases import UserTestCase
from jsonattrs.models import Attribute

from . import factories
from .. import models
from ..managers import create_children, create_options

path = os.path.dirname(settings.BASE_DIR)


class CreateChildrenTest(TestCase):

    def test_create_children_where_children_is_none(self):
        children = None
        create_children(children)

        assert models.QuestionGroup.objects.exists() is False
        assert models.Question.objects.exists() is False

    def test_create_children(self):
        questionnaire = factories.QuestionnaireFactory.create()
        children = [{
            'label': 'This form showcases the different question',
            'name': 'intro',
            'type': 'note'
        }, {
            'label': 'Text question type',
            'name': 'text_questions',
            'type': 'group',
            'children': [
                {
                    'hint': 'Can be short or long but '
                            'always one line (type = '
                            'text)',
                    'label': 'Text',
                    'name': 'my_string',
                    'type': 'text'
                }
            ],
        }]
        create_children(children, kwargs={'questionnaire': questionnaire})

        assert models.QuestionGroup.objects.filter(
            questionnaire=questionnaire).count() == 1
        assert models.Question.objects.filter(
            questionnaire=questionnaire).count() == 2
        assert models.Question.objects.filter(
            questionnaire=questionnaire,
            question_group__isnull=False).count() == 1

    def test_create_children_with_repeat_group(self):
        questionnaire = factories.QuestionnaireFactory.create()
        children = [{
            'label': 'This form showcases the different question',
            'name': 'intro',
            'type': 'note'
        }, {
            'label': 'Text question type',
            'name': 'text_questions',
            'type': 'repeat',
            'children': [
                {
                    'hint': 'Can be short or long but '
                            'always one line (type = '
                            'text)',
                    'label': 'Text',
                    'name': 'my_string',
                    'type': 'text'
                },
                {
                    'hint': 'Nested group',
                    'label': 'Group',
                    'name': 'my_group',
                    'type': 'group',
                    'children': [
                        {
                            'hint': 'More text',
                            'label': 'Text',
                            'name': 'my_group_string',
                            'type': 'text'
                        },
                    ]
                }
            ],
        }]
        create_children(children, kwargs={'questionnaire': questionnaire})

        assert models.QuestionGroup.objects.filter(
            questionnaire=questionnaire).count() == 1
        assert models.Question.objects.filter(
            questionnaire=questionnaire).count() == 3
        assert models.Question.objects.filter(
            questionnaire=questionnaire,
            question_group__isnull=False).count() == 1


class CreateOptionsTest(TestCase):

    def test_create_options(self):
        question = factories.QuestionFactory.create()
        options = [
            {'label': 'option 1', 'name': '1'},
            {'label': 'option 2', 'name': '2'},
            {'label': 'option 3', 'name': '3'}
        ]
        create_options(options, question)
        assert models.QuestionOption.objects.filter(
            question=question).count() == 3

    def test_create_options_with_empty_list(TestCase):
        errors = []
        question = factories.QuestionFactory.create(name='qu')
        create_options([], question, errors)
        assert "Please provide at least one option for field 'qu'" in errors


@pytest.mark.usefixtures('make_dirs')
class QuestionnaireManagerTest(TestCase):

    def test_create_from_form(self):
        storage = FakeS3Storage()
        file = open(
            path + '/questionnaires/tests/files/xls-form.xlsx', 'rb').read()
        form = storage.save('xls-forms/xls-form.xlsx', file)
        model = models.Questionnaire.objects.create_from_form(
            xls_form=form,
            original_file='original.xls',
            project=ProjectFactory.create()
        )
        assert model.id_string == 'question_types'
        assert model.filename == 'xls-form'
        assert model.title == 'Question types'
        assert model.original_file == 'original.xls'

    def test_update_from_form(self):
        storage = FakeS3Storage()
        file = open(
            path + '/questionnaires/tests/files/xls-form.xlsx', 'rb').read()
        form = storage.save('xls-forms/xls-form.xlsx', file)

        project = ProjectFactory.create()
        m1 = models.Questionnaire.objects.create_from_form(
            xls_form=form,
            project=project
        )

        model = models.Questionnaire.objects.create_from_form(
            xls_form=form,
            project=project
        )

        assert model.id_string == 'question_types'
        assert model.filename == 'xls-form'
        assert model.title == 'Question types'

        assert m1.id != model.id
        assert project.current_questionnaire == model.id

    def test_create_from_invald_form(self):
        storage = FakeS3Storage()
        file = open(path + '/questionnaires/tests/files/'
                           'xls-form-invalid.xlsx', 'rb').read()

        form = storage.save('xls-forms/xls-form-invalid.xlsx', file)
        with pytest.raises(InvalidXLSForm) as e:
            models.Questionnaire.objects.create_from_form(
                xls_form=form,
                project=ProjectFactory.create()
            )
        assert "Unknown question type 'interger'." in e.value.errors

        assert models.Questionnaire.objects.exists() is False
        assert models.QuestionGroup.objects.exists() is False
        assert models.Question.objects.exists() is False

    def test_insert_version_attr(self):
        xform = open(
            path + '/questionnaires/tests/files/ekcjvf464y5afks6b33qkct3.xml',
            'r').read()
        id_string = 'jurassic_park_survey'
        version = '2016072518593012'
        filename = 'ekcjvf464y5afks6b33qkct3'
        xml = models.Questionnaire.objects.insert_version_attribute(
            xform, filename, version
        )
        root = etree.fromstring(xml)
        ns = {'xf': 'http://www.w3.org/2002/xforms'}
        root_node = root.find(
            './/xf:instance/xf:{root_node}'.format(
                root_node=filename
            ), namespaces=ns
        )
        assert root_node is not None
        assert root_node.get('id') == id_string
        assert root_node.get('version') == version

    def test_unique_together_idstring_version(self):
        project = ProjectFactory.create()
        q1 = factories.QuestionnaireFactory.create(
            project=project,
            id_string='jurassic_park_survey'
        )
        version = q1.version
        with pytest.raises(IntegrityError):
            factories.QuestionnaireFactory.create(
                project=project,
                id_string='jurassic_park_survey',
                version=version
            )


class QuestionGroupManagerTest(TestCase):

    def test_create_from_dict(self):
        question_group_dict = {
            'label': 'Basic Select question types',
            'name': 'select_questions',
            'type': 'group'
        }
        questionnaire = factories.QuestionnaireFactory.create()

        model = models.QuestionGroup.objects.create_from_dict(
            dict=question_group_dict,
            questionnaire=questionnaire
        )
        assert model.questionnaire == questionnaire
        assert model.label == question_group_dict['label']
        assert model.name == question_group_dict['name']


class QuestionManagerTest(TestCase):

    def test_create_from_dict(self):
        question_dict = {
            'hint': 'For this field (type=integer)',
            'label': 'Integer',
            'name': 'my_int',
            'type': 'integer'
        }
        questionnaire = factories.QuestionnaireFactory.create()

        model = models.Question.objects.create_from_dict(
            dict=question_dict,
            questionnaire=questionnaire
        )

        assert model.question_group is None
        assert model.questionnaire == questionnaire
        assert model.label == question_dict['label']
        assert model.name == question_dict['name']
        assert model.type == 'IN'

    def test_create_from_dict_with_group(self):
        question_dict = {
            'hint': 'For this field (type=integer)',
            'label': 'Integer',
            'name': 'my_int',
            'type': 'integer'
        }
        questionnaire = factories.QuestionnaireFactory.create()
        question_group = factories.QuestionGroupFactory.create()

        model = models.Question.objects.create_from_dict(
            dict=question_dict,
            questionnaire=questionnaire,
            question_group=question_group
        )

        assert model.question_group is question_group
        assert model.questionnaire == questionnaire
        assert model.label == question_dict['label']
        assert model.name == question_dict['name']
        assert model.type == 'IN'


class MultilingualQuestionnaireTest(UserTestCase, TestCase):

    def _run(self, xlsxfile):
        storage = FakeS3Storage()
        file = open(
            path + '/questionnaires/tests/files/' + xlsxfile, 'rb'
        ).read()
        form = storage.save('xls-forms/' + xlsxfile, file)
        return models.Questionnaire.objects.create_from_form(
            xls_form=form,
            original_file='original.xls',
            project=ProjectFactory.create()
        )

    def test_no_default_language(self):
        with pytest.raises(InvalidXLSForm) as e:
            self._run('bad-no-default-language.xlsx')
        assert str(e.value) == ("Multilingual XLS forms must have "
                                "a default_language setting")

    def test_bad_default_language(self):
        with pytest.raises(InvalidXLSForm) as e:
            self._run('bad-bad-default-language.xlsx')
        assert str(e.value) == "Default language code 'Bengali' unknown"

    def test_bad_label_language(self):
        with pytest.raises(InvalidXLSForm) as e:
            self._run('bad-bad-label-language.xlsx')
        assert str(e.value) == "Label language code 'English' unknown"

    def test_multilingual_labels_and_choices(self):
        quest = self._run('ok-multilingual.xlsx')
        assert quest.default_language == 'en'
        q = quest.questions.get(name='gender')
        assert q.label == 'Gender'
        assert (sorted([(o.name, o.label) for o in q.options.all()]) ==
                [('female', 'Female'), ('male', 'Male')])
        a = Attribute.objects.get(name='gender')
        assert a.long_name == 'Gender'
        cd = a.choice_dict
        assert cd['female'] == 'Female'
        assert cd['male'] == 'Male'
        assert len(cd) == 2
        cur_language = get_language()
        try:
            activate('fr')
            assert q.label == 'Sexe'
            assert (sorted([(o.name, o.label) for o in q.options.all()]) ==
                    [('female', 'Femme'), ('male', 'Homme')])
            assert a.long_name == 'Sexe'
            cd = a.choice_dict
            assert cd['female'] == 'Femme'
            assert cd['male'] == 'Homme'
            assert len(cd) == 2
        finally:
            activate(cur_language)
