from jsonattrs.mixins import JsonAttrsMixin as TJsonAttrsMixin
from questionnaires.models import QuestionOption


class JsonAttrsMixin(TJsonAttrsMixin):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        project = context['object']
        vals = []
        for f in context[self.attributes_field]:
            options = QuestionOption.objects.filter(
                question__questionnaire_id=project.current_questionnaire,
                question__label=f[0])

            if options.exists():
                vals.append((f[0], options.get(name=f[1]).label))
            else:
                vals.append(f)
        context[self.attributes_field] = vals
        return context
