import pytest
import os
from django.test import TestCase
from django.conf import settings

from buckets.test.storage import FakeS3Storage
from buckets.test.mocks import ensure_dirs

from organization.tests.factories import ProjectFactory
from .. import models
from ..managers import create_children, create_options
from ..exceptions import InvalidXLSForm
from . import factories

path = os.path.dirname(settings.BASE_DIR)
ensure_dirs(add='s3/uploads/xls-forms')


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


class QuestionnaireManagerTest(TestCase):
    def test_current(self):
        project = ProjectFactory.create()
        factories.QuestionnaireFactory.create(version=1,
                                              project=project,
                                              name='questions')
        current = factories.QuestionnaireFactory.create(version=2,
                                                        project=project,
                                                        name='questions')

        questionnaire = models.Questionnaire.objects.current(
            project=project,
            name='questions'
        )
        assert questionnaire == current

    def test_create_from_form(self):
        ensure_dirs()

        storage = FakeS3Storage()
        file = open(
            path + '/questionnaires/tests/files/xls-form.xlsx', 'rb').read()
        form = storage.save('xls-forms/xls-form.xlsx', file)

        model = models.Questionnaire.objects.create_from_form(
            xls_form=form,
            project=ProjectFactory.create()
        )
        assert model.id_string == 'question_types'
        assert model.name == 'xls-form'
        assert model.title == 'Question types'
        assert model.version == 1

    def test_update_from_form(self):
        ensure_dirs()

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
        assert model.name == 'xls-form'
        assert model.title == 'Question types'
        assert model.version == 2

        assert m1.id != model.id
        assert m1.version == 1
        assert project.current_questionnaire == model.id

    def test_create_from_invald_form(self):
        ensure_dirs()

        storage = FakeS3Storage()
        file = open(path + '/questionnaires/tests/files/'
                           'xls-form-invalid.xlsx', 'rb').read()
        form = storage.save('xls-form-invalid.xlsx', file)

        with pytest.raises(InvalidXLSForm) as e:
            models.Questionnaire.objects.create_from_form(
                xls_form=form,
                project=ProjectFactory.create()
            )
        assert "'interger' is not an accepted question type" in e.value.errors

        assert models.Questionnaire.objects.exists() is False
        assert models.QuestionGroup.objects.exists() is False
        assert models.Question.objects.exists() is False


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
