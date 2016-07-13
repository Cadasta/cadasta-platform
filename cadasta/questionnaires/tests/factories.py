import factory
import hashlib

from core.tests.factories import ExtendedFactory
from organization.tests.factories import ProjectFactory
from ..models import Questionnaire, QuestionGroup, Question, QuestionOption


class QuestionnaireFactory(ExtendedFactory):
    class Meta:
        model = Questionnaire

    name = factory.Sequence(lambda n: "questionnaire_%s" % n)
    title = factory.Sequence(lambda n: "Questionnaire #%s" % n)
    id_string = factory.Sequence(lambda n: "q_id_%s" % n)
    xls_form = 'http://example.com/test.txt'
    xml_form = 'http://example.com/test.txt'
    version = 1
    md5_hash = hashlib.md5((str(id_string) + str(version)
                            ).encode()).hexdigest()
    project = factory.SubFactory(ProjectFactory)

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
    question = factory.SubFactory(QuestionFactory)
