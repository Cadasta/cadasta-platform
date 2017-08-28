from django.conf import settings
from django.utils.translation import ugettext as _
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.module_loading import import_string


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


def send_email_deleted_notification(email):
    msg_body = render_to_string(
        'allauth/account/messages/email_deleted.txt', {'email': email}
    )
    send_mail(
        _("Deleted email at Cadasta Platform"),
        msg_body,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def send_phone_update_notification(email):
    msg_body = render_to_string(
        'accounts/email/phone_changed_notification.txt')
    send_mail(
        _("Change of phone at Cadasta Platform"),
        msg_body,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def send_phone_deleted_notification(email):
    msg_body = render_to_string(
        'accounts/email/phone_deleted_notification.txt')
    send_mail(
        _("Deleted phone at Cadasta Platform"),
        msg_body,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def send_sms(to, body):
    twilioobj = (import_string(settings.SMS_GATEWAY))()
    twilioobj.send_sms(to, body)
