from organization.models import Project
from questionnaires.models import QuestionOption


class OptionLabelsFix:
    def add_attribute_fields(self, schema_selectors):
        super().add_attribute_fields(schema_selectors)

        strip_length = len(self.attributes_field) + 2
        prj = Project.objects.get(id=self.project_id)
        for f in self.fields:
            options = QuestionOption.objects.filter(
                    question__questionnaire_id=prj.current_questionnaire,
                    question__name=f[strip_length:])
            if options.exists():
                self.fields[f].choices = options.values_list('name', 'label')
