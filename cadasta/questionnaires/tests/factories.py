import os
import factory
import hashlib
from datetime import datetime
from buckets.test.storage import FakeS3Storage
from core.tests.factories import ExtendedFactory
from organization.tests.factories import ProjectFactory
from ..models import Questionnaire, QuestionGroup
from ..models import Question, QuestionOption, PDFForm
from accounts.tests.factories import UserFactory
from django.conf import settings

path = os.path.dirname(settings.BASE_DIR)


class QuestionnaireFactory(ExtendedFactory):
    class Meta:
        model = Questionnaire

    filename = factory.Sequence(lambda n: "questionnaire_%s" % n)
    title = factory.Sequence(lambda n: "Questionnaire #%s" % n)
    id_string = factory.Sequence(lambda n: "questionnaire_%s" % n)
    xls_form = 'http://example.com/test.txt'
    xml_form = 'http://example.com/test.txt'
    version = int(datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-4])
    md5_hash = hashlib.md5((str(filename) + str(id_string) + str(version)
                            ).encode()).hexdigest()
    project = factory.SubFactory(ProjectFactory)
    default_language = 'en'

    @factory.post_generation
    def add_current_questionnaire(self, create, extracted, **kwargs):
        self.project.current_questionnaire = self.id
        self.project.save()


class QuestionGroupFactory(ExtendedFactory):
    class Meta:
        model = QuestionGroup

    name = factory.Sequence(lambda n: "questiongroup_%s" % n)
    label = factory.Sequence(lambda n: "QuestionGroup #%s" % n)
    questionnaire = factory.SubFactory(QuestionnaireFactory)


class QuestionFactory(ExtendedFactory):
    class Meta:
        model = Question

    name = factory.Sequence(lambda n: "question_%s" % n)
    label = factory.Sequence(lambda n: "Question #%s" % n)
    type = 'IN'
    required = False
    constraint = ''
    questionnaire = factory.SubFactory(QuestionnaireFactory)
    question_group = factory.SubFactory(QuestionGroupFactory)


class QuestionOptionFactory(ExtendedFactory):
    class Meta:
        model = QuestionOption

    name = factory.Sequence(lambda n: "question_option_%s" % n)
    label = factory.Sequence(lambda n: "Question Option #%s" % n)
    index = factory.Sequence(lambda n: n)
    question = factory.SubFactory(QuestionFactory)


class PDFFormFactory(ExtendedFactory):

    class Meta:
        model = PDFForm

    name = factory.Sequence(lambda n: "PDFForm #%s" % n)
    description = factory.Sequence(lambda n: "PDF Form #%s description" % n)
    instructions = factory.Sequence(lambda n: "Test #%s instructions" % n)
    contributor = factory.SubFactory(UserFactory)
    project = factory.SubFactory(ProjectFactory)
    last_updated = datetime.now()
    questionnaire = factory.SubFactory(QuestionnaireFactory)

    @classmethod
    def _prepare(cls, create, **kwargs):
        pdfform = super()._prepare(create, **kwargs)

        if not pdfform.file.url:
            storage = FakeS3Storage()
            file = open(path + '/questionnaires/tests/files/image.jpg',
                        'rb').read()
            file_name = storage.save('pdf-form-logos/image.jpg', file)
            pdfform.file = file_name
            if create:
                pdfform.save()

        return pdfform
