import re
from django.conf import settings
from django.utils.translation import ugettext as _
from core.messages import SANITIZE_ERROR
from core.validators import sanitize_string
from .choices import QUESTION_TYPES, XFORM_GEOM_FIELDS


def validate_accuracy(val):
    """Returns True if the provided value is a positive float. """

    # bool can be casted to float that's why we check this first
    if isinstance(val, bool):
        return False

    try:
        val = float(val)
        if val > 0:
            return True
    except ValueError:
        pass

    return False


def gps_relevant(json):
    return json.get('type') in XFORM_GEOM_FIELDS


def validate_id_string(json):
    id_string = json.get('id_string', '')
    if not id_string or re.search(r"\s", id_string):
        return _("'id_string' cannot be blank or contain whitespace.")


def validate_type(type, value):
    if type == 'string':
        return isinstance(value, str)
    elif type == 'number':
        return (not isinstance(value, bool) and
                isinstance(value, (int, float)))
    elif type == 'integer':
        return not isinstance(value, bool) and isinstance(value, int)
    elif type == 'boolean':
        return isinstance(value, bool)
    elif type == 'array':
        return isinstance(value, list)


QUESTIONNAIRE_SCHEMA = {
    'title': {'type': 'string', 'required': True},
    'id_string': {'type': 'string', 'required': True},
    'default_language': {'type': 'string',
                         'required': True,
                         'enum': settings.FORM_LANGS.keys()},
}

QUESTION_SCHEMA = {
    'name': {'type': 'string', 'required': True},
    'label': {'type': 'string'},
    'type': {'type': 'string',
             'required': True,
             'enum': [c[0] for c in QUESTION_TYPES]},
    'required': {'type': 'boolean'},
    'constraint': {'type': 'string'},
    'index': {'type': 'integer', 'required': True},
    'gps_accuracy': {'type': 'number',
                     'function': validate_accuracy,
                     'errors': {
                        'function': _("gps_accuracy must be positve float")
                     },
                     'relevant': gps_relevant}
}

QUESTION_GROUP_SCHEMA = {
    'name': {'type': 'string', 'required': True},
    'label': {'type': 'string'},
    'type': {'type': 'string', 'required': True},
    'index': {'type': 'integer', 'required': True}
}

QUESTION_OPTION_SCHEMA = {
    'name': {'type': 'string', 'required': True},
    'label': {'type': 'string', 'required': True},
    'index': {'type': 'integer', 'required': True}
}


def validate_schema(schema, json):
    errors = {}
    for key, reqs in schema.items():
        item_errors = []
        item = json.get(key, None)

        if reqs.get('relevant') and not reqs['relevant'](json):
            continue

        if reqs.get('required', False) and item is None:
            item_errors.append(_("This field is required."))
        elif item:

            if not validate_type(reqs.get('type'), item):
                item_errors.append(
                    _("Value must be of type {}.").format(reqs.get('type')))

            if reqs.get('enum') and item not in reqs.get('enum'):
                item_errors.append(
                    _("{} is not an accepted value.").format(item))

            if reqs.get('function') and not reqs['function'](item):
                error = _("Validator {} did not validate.").format(
                    reqs['function'].__name__)
                if reqs.get('errors') and reqs['errors'].get('function'):
                    error = reqs['errors']['function']
                item_errors.append(error)

            if not sanitize_string(item):
                item_errors.append(SANITIZE_ERROR)

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

    if not errors.get('id_string'):
        id_errors = validate_id_string(json)
        if id_errors:
            errors['id_string'] = id_errors

    question_errs = validate_questions(json.get('questions', []))
    if any([q for q in question_errs]):
        errors['questions'] = question_errs

    group_errs = validate_question_groups(json.get('question_groups', []))
    if any([q for q in group_errs]):
        errors['question_groups'] = group_errs

    if errors:
        return errors


valid_relevent = (
    r"^(?P<is_not>not\()?"
    "((\$\{\w+\}\s?(=|>|<|>=|<=|!=)\s?(('|\"|“|‘)\w+('|\"|”|’)|[0-9]*))|"
    "(selected\(\$\{\w+\},\s?(('|\"|“|‘)\w+('|\"|”|’)|[0-9]*)\)))"
    "(?(is_not)\))$"
)


def validate_relevant(relevant):
    segments = re.split(r"\sand\s|\sor\s", relevant)
    return all(re.match(valid_relevent, s) for s in segments)
