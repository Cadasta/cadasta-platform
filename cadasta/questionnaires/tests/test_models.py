from django.test import TestCase
from core.tests.utils.cases import UserTestCase
from accounts.tests.factories import UserFactory
from organization.tests.factories import ProjectFactory
from . import factories


class QuestionnaireTest(TestCase):
    def test_repr(self):
        project = ProjectFactory.create(slug='prj')
        questionnaire = factories.QuestionnaireFactory.build(id='abc123',
                                                             project=project,
                                                             title='Questions')
        assert repr(questionnaire) == ('<Questionnaire id=abc123 '
                                       'title=Questions project=prj>')

    def test_save(self):
        questionnaire = factories.QuestionnaireFactory.build(
            project=ProjectFactory.create()
        )
        questionnaire.version = None
        questionnaire.md5_hash = None

        questionnaire.save()
        assert questionnaire.version is not None
        assert questionnaire.md5_hash is not None

        questionnaire = factories.QuestionnaireFactory.build(
            version=129839021903,
            md5_hash='sakohjd89su90us9a0jd90sau90d',
            project=ProjectFactory.create()
        )

        questionnaire.save()
        assert questionnaire.version == 129839021903
        assert questionnaire.md5_hash == 'sakohjd89su90us9a0jd90sau90d'


class QuestionGroupTest(TestCase):
    def test_repr(self):
        questionnaire = factories.QuestionnaireFactory.create(id='abc123')
        group = factories.QuestionGroupFactory.build(
            id='abc123', name='Group', questionnaire=questionnaire)
        assert repr(group) == ('<QuestionGroup id=abc123 name=Group '
                               'questionnaire=abc123>')


class QuestionTest(TestCase):
    def test_repr(self):
        group = factories.QuestionGroupFactory.create(id='abc123')
        questionnaire = factories.QuestionnaireFactory.create(id='abc123')
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
        question = factories.QuestionFactory.create(id='abc123')
        option = factories.QuestionOptionFactory(id='abc123', name='Option',
                                                 question=question)
        assert repr(option) == ('<QuestionOption id=abc123 name=Option '
                                'question=abc123>')


class PDFFormTest(UserTestCase, TestCase):
    def test_str(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        pdfform = factories.PDFFormFactory.create(id='abc123',
                                                  project=project,
                                                  contributor=user)
        assert pdfform.name is not None
        assert pdfform.id == 'abc123'
        assert pdfform.file.url == '/media/s3/uploads/pdf-form-logos/image.jpg'
