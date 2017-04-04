from django.conf import settings
from django.utils.translation import ugettext as _
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_email_update_notification(email):
    msg_body = render_to_string(
        'accounts/email/email_changed_notification.txt')
    send_mail(
        _("Change of email at Cadasta Platform"),
        msg_body,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
