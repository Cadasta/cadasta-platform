import string
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _


DEFAULT_CHARACTER_TYPES = [
            string.ascii_lowercase,
            string.ascii_uppercase,
            string.punctuation,
            string.digits
        ]


class CharacterTypePasswordValidator(object):
    def __init__(self, character_types=DEFAULT_CHARACTER_TYPES,
                 unique_types=3):
        self.character_types = character_types
        self.unique_types = unique_types

    def error_message(self):
        return _((
            "Passwords must contain at least {unique_types} of the following "
            " {character_types} character types:\n"
            "lowercase characters, uppercase characters, "
            "special characters, "
            "and/or numerical character.\n").format(
            unique_types=self.unique_types,
            character_types=len(self.character_types)))

    def validate(self, password, user=None):
        errors = 0

        for character_type in self.character_types:
            if len(set(character_type).intersection(password)) == 0:
                errors += 1

        if len(self.character_types) - self.unique_types < errors:
            raise ValidationError(self.error_message())


class EmailSimilarityValidator(object):
    def validate(self, password, user=None):
        if not user:
            return None

        email = user.email.lower().split('@')
        if email[0] in password:
            raise ValidationError(
                _("Passwords cannot contain your email."))
