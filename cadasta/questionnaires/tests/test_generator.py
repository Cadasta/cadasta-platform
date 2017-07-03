from django.test import TestCase
from organization.tests.factories import ProjectFactory
from .factories import PDFFormFactory, QuestionnaireFactory
from core.tests.utils.cases import UserTestCase
from ..managers import create_children
from ..download.generator import PDFGenerator


class PDFFormGenerateTest(UserTestCase, TestCase):

    def test_pdf_generation(self):
        project = ProjectFactory.create()
        questionnaire = QuestionnaireFactory.create(project=project)
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
        pdfform = PDFFormFactory.create(project=project)
        generator = PDFGenerator(project, pdfform)
        absolute_url = ""
        pdf = generator.generate_pdf(absolute_url)
        assert pdf is not None
