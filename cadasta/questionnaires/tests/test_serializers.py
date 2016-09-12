import pytest
import os
from django.test import TestCase
from django.conf import settings

from buckets.test.storage import FakeS3Storage

from organization.tests.factories import ProjectFactory
from questionnaires.exceptions import InvalidXLSForm
from core.tests.utils.files import make_dirs  # noqa

from . import factories
from .. import serializers
from ..models import Questionnaire

path = os.path.dirname(settings.BASE_DIR)


@pytest.mark.usefixtures('make_dirs')
class QuestionnaireSerializerTest(TestCase):
    def _get_form(self, form_name):

        storage = FakeS3Storage()
        file = open(
            path + '/questionnaires/tests/files/{}.xlsx'.format(form_name),
            'rb'
        ).read()
        form = storage.save('xls-forms/{}.xlsx'.format(form_name), file)
        return form

    def test_deserialize(self):
        form = self._get_form('xls-form')

        project = ProjectFactory.create()

        serializer = serializers.QuestionnaireSerializer(
            data={'xls_form': form},
            context={'project': project}
        )
        assert serializer.is_valid(raise_exception=True) is True
        serializer.save()

        assert Questionnaire.objects.count() == 1
        questionnaire = Questionnaire.objects.first()

        assert questionnaire.id_string == 'question_types'
        assert questionnaire.filename == 'xls-form'
        assert questionnaire.title == 'Question types'

        assert serializer.data['id'] == questionnaire.id
        assert serializer.data['filename'] == questionnaire.filename
        assert serializer.data['title'] == questionnaire.title
        assert serializer.data['id_string'] == questionnaire.id_string
        assert serializer.data['xls_form'] == questionnaire.xls_form.url
        assert serializer.data['xml_form'] == questionnaire.xml_form.url
        assert serializer.data['version'] == questionnaire.version
        assert len(serializer.data['questions']) == 1

    def test_deserialize_invalid_form(self):
        form = self._get_form('xls-form-invalid')

        project = ProjectFactory.create()

        serializer = serializers.QuestionnaireSerializer(
            data={'xls_form': form},
            context={'project': project}
        )
        assert serializer.is_valid(raise_exception=True) is True
        with pytest.raises(InvalidXLSForm):
            serializer.save()
        assert Questionnaire.objects.count() == 0

    def test_serialize(self):
        questionnaire = factories.QuestionnaireFactory()
        serializer = serializers.QuestionnaireSerializer(questionnaire)

        assert serializer.data['id'] == questionnaire.id
        assert serializer.data['filename'] == questionnaire.filename
        assert serializer.data['title'] == questionnaire.title
        assert serializer.data['id_string'] == questionnaire.id_string
        assert serializer.data['xls_form'] == questionnaire.xls_form.url
        assert serializer.data['xml_form'] == questionnaire.xml_form.url
        assert serializer.data['version'] == questionnaire.version
        assert 'project' not in serializer.data


class QuestionGroupSerializerTest(TestCase):
    def test_serialize(self):
        questionnaire = factories.QuestionnaireFactory()
        question_group = factories.QuestionGroupFactory.create(
            questionnaire=questionnaire)
        factories.QuestionFactory.create_batch(
            2,
            questionnaire=questionnaire,
            question_group=question_group
        )
        not_in = factories.QuestionFactory.create(
            questionnaire=questionnaire
        )
        question_group.refresh_from_db()

        serializer = serializers.QuestionGroupSerializer(question_group)
        assert serializer.data['id'] == question_group.id
        assert serializer.data['name'] == question_group.name
        assert serializer.data['label'] == question_group.label
        assert len(serializer.data['questions']) == 2
        assert not_in.id not in [q['id'] for q in serializer.data['questions']]
        assert 'questionnaire' not in serializer.data


class QuestionSerializerTest(TestCase):
    def test_serialize(self):
        question = factories.QuestionFactory.create()
        serializer = serializers.QuestionSerializer(question)

        assert serializer.data['id'] == question.id
        assert serializer.data['name'] == question.name
        assert serializer.data['label'] == question.label
        assert serializer.data['type'] == question.type
        assert serializer.data['required'] == question.required
        assert serializer.data['constraint'] == question.constraint
        assert 'options' not in serializer.data
        assert 'questionnaire' not in serializer.data
        assert 'question_group' not in serializer.data

    def test_serialize_with_options(self):
        question = factories.QuestionFactory.create(type='S1')
        factories.QuestionOptionFactory.create_batch(2, question=question)
        serializer = serializers.QuestionSerializer(question)

        assert serializer.data['id'] == question.id
        assert serializer.data['name'] == question.name
        assert serializer.data['label'] == question.label
        assert serializer.data['type'] == question.type
        assert serializer.data['required'] == question.required
        assert serializer.data['constraint'] == question.constraint
        assert len(serializer.data['options']) == 2
        assert 'questionnaire' not in serializer.data
        assert 'question_group' not in serializer.data


class QuestionOptionSerializerTest(TestCase):
    def test_serialize(self):
        question_option = factories.QuestionOptionFactory.create()
        serializer = serializers.QuestionOptionSerializer(question_option)

        assert serializer.data['id'] == question_option.id
        assert serializer.data['name'] == question_option.name
        assert serializer.data['label'] == question_option.label
        assert 'question' not in serializer.data
