from django.utils.translation import ugettext as _


phone_format = _(
    "Phone numbers must be provided in the format +9999999999."
    " Up to 15 digits allowed. Do not include hyphen or"
    " blank spaces in between, at the beginning or at the end."
)

account_inactive = _(
    "Your account has been set inactive. We request you to verify"
    " your registered phone or email in order to access your account.")


unverified_identifier = _(
    "You have not verified your phone or email. We request you to verify"
    " your registered phone or email in order to access your account.")
