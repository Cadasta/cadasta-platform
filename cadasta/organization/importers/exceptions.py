from django.utils.translation import ugettext as _


class DataImportError(Exception):
    def __init__(self, message, line_num=None):
        super(DataImportError, self).__init__(message)
        self.line_num = line_num

    def __str__(self):
        if self.line_num:
            return _("Error importing file at line %d: %s" % (
                self.line_num, self.args[0])
            )
        else:
            return _("Error importing file: %s" % self.args[0])
