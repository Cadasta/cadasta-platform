from django.utils.translation import ugettext as _


class DataImportError(Exception):
    def __init__(self, line_num, error, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.error = error
        self.line_num = line_num

    def __str__(self):
        return _("Error importing file at line %d: %s" % (
            self.line_num, self.error)
        )
