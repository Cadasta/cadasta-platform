from django.utils.translation import ugettext as _


phone_format = _(
    "Your phone number must start with +, followed by a "
    " country code and phone number with no spaces or "
    " punctuation. It must contain between 5 and 14 digits."
)

account_inactive = _(
    "Your account has been set inactive. We request you to verify"
    " your registered phone or email in order to access your account.")


unverified_identifier = _(
    "You have not verified your phone or email. We request you to verify"
    " your registered phone or email in order to access your account.")

# send an sms to the user's phone(if any) notifying the removal of email
email_delete = _(
    "You are receiving this message because a user at Cadasta Platform removed"
    " the email address from the account linked to this phone number."
    " If it wasn't you, please contact us immediately at security@cadasta.org")

# send an sms to the user's phone(if any) notifying the change in email
email_change = _(
    "You are receiving this message because a user at Cadasta Platform updated"
    " the email address for the account linked to this phone"
    " number."
    " If it wasn't you, please contact us immediately at security@cadasta.org")

# send an sms to the user's old phone(if any) notifying the removal of phone
phone_delete = _(
    "You are receiving this message because a user at Cadasta Platform removed"
    " the phone number from the account previously linked to this"
    " phone number."
    " If it wasn't you, please contact us immediately at security@cadasta.org")

# send an sms to the user's old phone(if any) notifying the change in phone
phone_change = _(
    "You are receiving this message because a user at Cadasta Platform changed"
    " the phone number for the account previously linked to this"
    " phone number."
    " If it wasn't you, please contact us immediately at security@cadasta.org")

# send an sms to the user's phone notifying the change in password
password_change_or_reset = _(
    "You are receiving this message because a user at Cadasta Platform has"
    " changed or reset the password for your account linked to this phone"
    " number."
    " If it wasn't you, please contact us immediately at security@cadasta.org")
