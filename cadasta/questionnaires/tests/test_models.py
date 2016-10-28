from django.test import TestCase
from organization.tests.factories import ProjectFactory
from . import factories


class QuestionnaireTest(TestCase):
    def test_repr(self):
        project = ProjectFactory.build(slug='prj')
        questionnaire = factories.QuestionnaireFactory.build(id='abc123',
                                                             project=project,
                                                             title='Questions')
        assert repr(questionnaire) == ('<Questionnaire id=abc123 '
                                       'title=Questions project=prj>')


class QuestionGroupTest(TestCase):
    def test_repr(self):
        questionnaire = factories.QuestionnaireFactory.build(id='abc123')
        group = factories.QuestionGroupFactory.build(
            id='abc123', name='Group', questionnaire=questionnaire)
        assert repr(group) == ('<QuestionGroup id=abc123 name=Group '
                               'questionnaire=abc123>')


class QuestionTest(TestCase):
    def test_repr(self):
        group = factories.QuestionGroupFactory.build(id='abc123')
        questionnaire = factories.QuestionnaireFactory.build(id='abc123')
        question = factories.QuestionFactory.build(id='abc123',
                                                   name='Question',
                                                   question_group=group,
                                                   questionnaire=questionnaire)
        assert repr(question) == ('<Question id=abc123 name=Question '
                                  'questionnaire=abc123 '
                                  'question_group=abc123>')

    def test_has_options(self):
        question = factories.QuestionFactory.create(type='S1')
        assert question.has_options is True

        question = factories.QuestionFactory.create(type='SM')
        assert question.has_options is True

        question = factories.QuestionFactory.create(type='IN')
        assert question.has_options is False


class QuestionOptionTest(TestCase):
    def test_repr(self):
        question = factories.QuestionFactory.build(id='abc123')
        option = factories.QuestionOptionFactory(id='abc123', name='Option',
                                                 question=question)
        assert repr(option) == ('<QuestionOption id=abc123 name=Option '
                                'question=abc123>')
