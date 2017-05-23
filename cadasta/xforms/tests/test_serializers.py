import pytest

from django.test import TestCase
from django.core.urlresolvers import reverse
from rest_framework.test import APIRequestFactory, force_authenticate

from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from core.tests.utils.files import make_dirs  # noqa
from organization.tests.factories import ProjectFactory
from questionnaires.serializers import QuestionnaireSerializer
from questionnaires.models import Questionnaire
from accounts.tests.factories import UserFactory
from .. import serializers


@pytest.mark.usefixtures('make_dirs')
class XFormListSerializerTest(UserTestCase, FileStorageTestCase, TestCase):
    def _test_serialize(self, https=False):
        form = self.get_form('xls-form')
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
        url_refix = 'https' if https else 'http'

        assert serializer.data['formID'] == questionnaire.data['id_string']
        assert serializer.data['name'] == questionnaire.data['title']
        assert serializer.data['version'] == questionnaire.data['version']
        assert (serializer.data['downloadUrl'] ==
                url_refix + '://testserver' +
                reverse('form-download', args=[form.id]))
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
