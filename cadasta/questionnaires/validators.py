from django.utils.translation import ugettext as _
from .models import Question

QUESTIONNAIRE_SCHEMA = {
    'title': {'type': 'string', 'required': True},
    'id_string': {'type': 'string', 'required': True},
}

QUESTION_SCHEMA = {
      'name': {'type': 'string', 'required': True},
      'label': {'type': 'string'},
      'type': {'type': 'string',
               'required': True,
               'enum': [c[0] for c in Question.TYPE_CHOICES]},
      'required': {'type': 'boolean'},
      'constraint': {'type': 'string'}
}

QUESTION_GROUP_SCHEMA = {
    'name': {'type': 'string', 'required': True},
    'label': {'type': 'string'},
    'type': {'type': 'string', 'required': True},
}

QUESTION_OPTION_SCHEMA = {
    'name': {'type': 'string', 'required': True},
    'label': {'type': 'string', 'required': True},
}


def validate_type(type, value):
    if type == 'string':
        return isinstance(value, str)
    elif type == 'number':
        return ((not isinstance(value, bool) and
                 isinstance(value, (int, float))))
    elif type == 'boolean':
        return isinstance(value, bool)
    elif type == 'array':
        return isinstance(value, list)


def validate_schema(schema, json):
    errors = {}
    for key, reqs in schema.items():
        item_errors = []
        item = json.get(key, None)

        if reqs.get('required', False) and not item:
            item_errors.append(_("This field is required."))
        elif item:
            if not validate_type(reqs.get('type'), item):
                item_errors.append(
                    _("Value must be of type {}.").format(reqs.get('type')))
            if reqs.get('enum') and item not in reqs.get('enum'):
                item_errors.append(
                    _("{} is not an accepted value.").format(item))

        if item_errors:
            errors[key] = item_errors

    return errors


def validate_question_options(options):
    errors = []

    for option in options:
        errors.append(validate_schema(QUESTION_OPTION_SCHEMA, option))

    return errors


def validate_questions(questions):
    errors = []

    for question in questions:
        question_errs = validate_schema(QUESTION_SCHEMA, question)
        option_errs = validate_question_options(question.get('options', []))

        if any([o for o in option_errs]):
            question_errs['options'] = option_errs
        errors.append(question_errs)

    return errors


def validate_question_groups(groups):
    errors = []

    for group in groups:
        group_errs = validate_schema(QUESTION_GROUP_SCHEMA, group)

        questions_errs = validate_questions(group.get('questions', []))
        if any([q for q in questions_errs]):
            group_errs['questions'] = questions_errs

        questions_group_errs = validate_question_groups(
            group.get('question_groups', []))
        if any([q for q in questions_group_errs]):
            group_errs['question_groups'] = questions_group_errs

        errors.append(group_errs)

    return errors


def validate_questionnaire(json):
    errors = validate_schema(QUESTIONNAIRE_SCHEMA, json)

    question_errs = validate_questions(json.get('questions', []))
    if any([q for q in question_errs]):
        errors['questions'] = question_errs

    group_errs = validate_question_groups(json.get('question_groups', []))
    if any([q for q in group_errs]):
        errors['question_groups'] = group_errs

    if errors:
        return errors
