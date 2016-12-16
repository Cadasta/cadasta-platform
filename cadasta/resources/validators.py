from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

ACCEPTED_TYPES = settings.ICON_LOOKUPS.keys()


def validate_file_type(type):
    if type not in ACCEPTED_TYPES:
        raise ValidationError(
            _("Files of type {mime} are not accepted.").format(mime=type)
        )
