import pytest
from django.test import TestCase
from .. import forms
from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from core.tests.utils.files import make_dirs  # noqa
from accounts.tests.factories import UserFactory
from organization.tests.factories import ProjectFactory
from .factories import PDFFormFactory, QuestionnaireFactory
from ..models import PDFForm
from resources.tests.utils import clear_temp  # noqa


@pytest.mark.usefixtures('make_dirs')
@pytest.mark.usefixtures('clear_temp')
class PDFFormFormTest(UserTestCase, FileStorageTestCase, TestCase):
    def setUp(self):
        super().setUp()
        file = self.get_file('/questionnaires/tests/files/image.jpg', 'rb')
        file_name = self.storage.save('pdf-form-logos/image.jpg', file)

        self.data = {
            'name': 'Some name',
            'description': '',
            'instructions': '',
            'file': file_name,
        }
        self.project = ProjectFactory.create()

    def _get_form(self, form_name):
        file = self.get_file(
            '/questionnaires/tests/files/{}.xlsx'.format(form_name),
            'rb')
        form = self.storage.save('xls-forms/{}.xlsx'.format(form_name), file)
        return form

    def _save(self, data, count=1):
        user = UserFactory.create()
        questionnaire = QuestionnaireFactory.create(
            project=self.project,
            xls_form=self._get_form('xls-form'))

        form = forms.PDFFormCreateForm(self.data,
                                       contributor=user,
                                       questionnaire=questionnaire,
                                       project_id=self.project.id)
        form.save()
        assert form.is_valid() is True
        assert PDFForm.objects.count() == count

    def test_create_pdfform(self):
        self._save(self.data)
        pdfform = PDFForm.objects.first()
        assert pdfform.name == 'Some name'

    def test_update_pdfform(self):
        pdfform = PDFFormFactory.create(id='abc123')
        self.data['description'] = 'Form description'
        form = forms.PDFFormCreateForm(self.data, instance=pdfform)
        form.save()
        pdfform.refresh_from_db()

        assert form.is_valid() is True
        assert pdfform.description == self.data['description']
