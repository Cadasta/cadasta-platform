import logging

from django.conf import settings
from twilio.rest import Client, TwilioException

fake_logger = logging.getLogger(name='accounts.FakeGateway')


class TwilioGateway(object):

    def __init__(self,
                 account_sid=settings.TWILIO_ACCOUNT_SID,
                 auth_token=settings.TWILIO_AUTH_TOKEN,
                 from_phone_number_list=[]):

        self.client = Client(account_sid, auth_token)
        self.from_phone_number_list = from_phone_number_list

    def send_sms(self, to, body):
        try:
            # create and send a message with client
            message = self.client.messages.create(
                to=to,
                from_=settings.TWILIO_PHONE,
                body=body)

        except TwilioException as e:
            message = e

        return message


class FakeGateway(object):

    def send_sms(self, to, body):
        fake_logger.debug("Message sent to: {phone}. Message: {body}".format(
            phone=to, body=body))
