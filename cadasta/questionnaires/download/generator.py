from questionnaires.models import Questionnaire
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
import logging

EXCLUDE_GEO_FIELDS = [
    'geo_type', 'location_geoshape', 'location_geotrace', 'location_geometry'
]


class PDFGenerator():
    def __init__(self, project, pdfform):
        self.project = project
        self.pdfform = pdfform

    def generate_pdf(self, absolute_uri):
        logging.getLogger('weasyprint').setLevel(100)
        template_questions_list = []
        template_question_groups_list = []
        pdf = None

        questionnaire = Questionnaire.objects.get(
            id=self.project.current_questionnaire)
        questions_list = questionnaire.questions.all()
        template_question_groups_list = questionnaire.question_groups.all()

        for question in questions_list:
            if question.question_group is None:
                template_questions_list.append(question)

        if questionnaire is not None:
            html_string = render_to_string('questionnaires/'
                                           'pdf_form_generator.html',
                                           {'questionnaire': questionnaire,
                                            'questions_list':
                                                template_questions_list,
                                            'question_groups_list':
                                                template_question_groups_list,
                                            'exclude_geo_fields':
                                                EXCLUDE_GEO_FIELDS,
                                            'pdfform': self.pdfform})
            html = HTML(string=html_string, base_url=absolute_uri)
            pdf = html.write_pdf(stylesheets=[
                CSS(string='@page { size: A4; margin: 2cm };'
                           '* { float: none !important; };'
                           '@media print '
                           '{ nav { display: none; } }')
            ])

        return pdf
