from django.core.exceptions import ValidationError

from jsonschema import Draft4Validator

from core.exceptions import JsonValidationError
from core.validators import validate_json


SCHEMA_CONTACT = {
    "$schema": "http://json-schema.org/schema#",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "email": {"type": ["string", "null"], "format": "email"},
        "url": {"type": "string", "format": "uri"},
        "street-address": {"type": "string"},
        "locality": {"type": "string"},
        "postal-code": {"type": "string"},
        "country-name": {"type": "string"},
        "tel": {"type": ["string", "null"]},
        "job-title": {"type": "string"}
    },
    "anyOf": [
        {"required": ["email"]},
        {"required": ["tel"]}
    ],
    "required": ["name"]
}
Draft4Validator.check_schema(SCHEMA_CONTACT)


def validate_contact(value):
    errors = []
    if not isinstance(value, list):
        value = (value, )

    for item in value:
        try:
            validate_json(item, SCHEMA_CONTACT)
        except JsonValidationError as e:
            errors.append(e)

    if errors:
        raise ValidationError(errors)
