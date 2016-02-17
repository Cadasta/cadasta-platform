import pytest
from django.test import TestCase
from ..validators import validate_json, JsonValidationError


class ValidationTest(TestCase):
    def test_validate_valid(self):
        schema = {
            "$schema": "http://json-schema.org/schema#",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
            "required": ["name"]
        }

        assert validate_json({'name': 'val'}, schema) is None

    def test_validate_anyof(self):
        schema = {
            "$schema": "http://json-schema.org/schema#",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
            },
            "anyOf": [
                {"required": ["name"]},
                {"required": ["description"]},
            ]
        }

        with pytest.raises(JsonValidationError) as exc:
            assert validate_json({}, schema) is None

        assert exc.value.errors['name'] == (
            "Please provide either name or description")
        assert exc.value.errors['description'] == (
            "Please provide either name or description")

    def test_validate_invalid_required(self):
        schema = {
            "$schema": "http://json-schema.org/schema#",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
            "required": ["name"]
        }

        with pytest.raises(JsonValidationError) as exc:
            validate_json({'some': 'val'}, schema)

        assert exc.value.errors['name'] == "This field is required."

    def test_validate_invalid_format(self):
        schema = {
            "$schema": "http://json-schema.org/schema#",
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
            },
        }

        with pytest.raises(JsonValidationError) as exc:
            validate_json({'email': 'blah'}, schema)

        assert exc.value.errors['email'] == "'blah' is not a 'email'"
