import magic
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

ACCEPTED_TYPES = ['application/pdf', 'audio/mpeg3', 'audio/x-mpeg-3',
                  'video/mpeg', 'video/x-mpeg', 'application/msword',
                  'image/jpeg', 'image/png']


def validate_file_type(file):
    mime = magic.from_file(file.open().name, mime=True).decode()
    if mime not in ACCEPTED_TYPES:
        raise ValidationError(
            _("Files of type {mime} are not accpeted.").format(mime=mime)
        )
