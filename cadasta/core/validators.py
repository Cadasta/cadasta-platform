from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from emoji import UNICODE_EMOJI
from jsonschema import Draft4Validator, FormatChecker
from .exceptions import JsonValidationError


def validate_json(value, schema):
    v = Draft4Validator(schema, format_checker=FormatChecker())
    errors = sorted(v.iter_errors(value), key=lambda e: e.path)

    message_dict = {}
    for e in errors:
        if e.validator == 'anyOf':
            fields = [
                f.message.split(' ')[0].replace('\'', '') for f in e.context
            ]

            for f in fields:
                message_dict[f] = _("Please provide either {}").format(
                    _(" or ").join(fields))

        elif e.validator == 'required':
            field = e.message.split(' ')[0].replace('\'', '')
            message_dict[field] = _("This field is required.")
        else:
            field = '.'.join([str(el) for el in e.path])
            message_dict[field] = e.message

    if message_dict:
        raise JsonValidationError(message_dict)


def validate_no_emoji(value):
    if any(s in UNICODE_EMOJI for s in value):
        raise ValidationError(
            _("Please do not include any emoji."))
