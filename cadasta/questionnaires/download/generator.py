import logging

from django.template.loader import render_to_string
from questionnaires.models import Questionnaire


EXCLUDE_GEO_FIELDS = [
    'geo_type', 'location_geoshape', 'location_geotrace', 'location_geometry'
]


class PDFGenerator():

    def __init__(self, project, pdfform):
        self.project = project
        self.pdfform = pdfform

    def generate_pdf(self, absolute_uri):
        # suppress weasyprint logging
        logger = logging.getLogger("weasyprint")
        if not logger.handlers:
            logger.addHandler(logging.NullHandler())
        from weasyprint import HTML

        template_questions_list = []
        template_question_groups_list = []
        pdf = None

        questionnaire = Questionnaire.objects.get(
            id=self.project.current_questionnaire)
        questions_list = questionnaire.questions.all()
        template_question_groups_list = questionnaire.question_groups.all()

        [template_questions_list.append(question)
            for question in questions_list if question.question_group is None]

        html_string = render_to_string('questionnaires/'
                                       'pdf_form_generator.html',
                                       {'questionnaire': questionnaire,
                                        'questions_list':
                                            template_questions_list,
                                        'question_groups_list':
                                            template_question_groups_list,
                                        'exclude_geo_fields':
                                            EXCLUDE_GEO_FIELDS,
                                        'pdfform': self.pdfform,
                                        'thumbnail_url':
                                        self.pdfform.thumbnail})
        html = HTML(string=html_string, base_url=absolute_uri)
        pdf = html.write_pdf()

        return pdf
