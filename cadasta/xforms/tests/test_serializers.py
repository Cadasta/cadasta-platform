import pytest
import os
from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from buckets.test.storage import FakeS3Storage

from core.tests.utils.cases import UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from organization.tests.factories import ProjectFactory
from questionnaires.serializers import QuestionnaireSerializer
from questionnaires.models import Questionnaire
from accounts.tests.factories import UserFactory
from .. import serializers

path = os.path.dirname(settings.BASE_DIR)


@pytest.mark.usefixtures('make_dirs')
class XFormListSerializerTest(UserTestCase, TestCase):
    def _get_form(self, form_name):
        storage = FakeS3Storage()
        file = open(
            path + '/questionnaires/tests/files/{}.xlsx'.format(form_name),
            'rb'
        ).read()
        form = storage.save('xls-forms/{}.xlsx'.format(form_name), file)
        return form

    def _test_serialize(self, https=False):
        form = self._get_form('xls-form')
        self.url = '/collect/'
        user = UserFactory.create()
        request = APIRequestFactory().get(self.url)
        force_authenticate(request, user=user)
        if https:
            request.META['SERVER_PROTOCOL'] = 'HTTPS/1.1'
        project = ProjectFactory.create()
        questionnaire = QuestionnaireSerializer(
            data={'xls_form': form},
            context={'project': project}
        )

        assert questionnaire.is_valid(raise_exception=True) is True
        questionnaire.save()
        form = Questionnaire.objects.get(filename__contains='xls-form')

        serializer = serializers.XFormListSerializer(
            form, context={'request': request})

        assert serializer.data['formID'] == questionnaire.data['id_string']
        assert serializer.data['name'] == questionnaire.data['title']
        assert serializer.data['version'] == questionnaire.data['version']
        protocol = 'https' if https else 'http'
        assert (serializer.data['downloadUrl'] ==
                protocol + '://localhost:8000' +
                questionnaire.data['xml_form'])
        assert serializer.data['hash'] == questionnaire.data['md5_hash']

    def test_serialize(self):
        self._test_serialize()

    def test_https_serialize(self):
        self._test_serialize(https=True)

    def test_empty_serializer(self):
        serializer = serializers.XFormListSerializer()
        assert serializer.data['formID'] == ''
        assert 'downloadUrl' not in serializer.data.keys()
        assert serializer.data['hash'] == ''


class XFormSubmissionSerializerTest(UserTestCase):
    pass
