import magic
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

ACCEPTED_TYPES = [
    'application/pdf', 'audio/mpeg3', 'audio/x-mpeg-3', 'video/mpeg',
    'video/x-mpeg', 'image/jpeg', 'image/png', 'image/gif', 'image/tiff',
    'application/msword', 'application/msexcel', 'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']


def validate_file_type(file):
    mime = magic.from_file(file.open().name, mime=True).decode()
    if mime not in ACCEPTED_TYPES:
        raise ValidationError(
            _("Files of type {mime} are not accepted.").format(mime=mime)
        )
