from django.utils.translation import ugettext as _


class EmailNotVerifiedError(Exception):

    def __init__(self, msg=None):
        if not msg:
            self.msg = _("The email has not been verified.")
        super().__init__(msg)


class PhoneNotVerifiedError(Exception):

    def __init__(self, msg=None):
        if not msg:
            self.msg = _("The phone has not been verified.")
        super().__init__(msg)


class AccountInactiveError(Exception):

    def __init__(self, msg=None):
        if not msg:
            self.msg = _("User account is disabled.")
        super().__init__(msg)
