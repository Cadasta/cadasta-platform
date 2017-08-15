import random
import logging

from django.conf import settings
from twilio.rest import Client, TwilioException

twilio_logger = logging.getLogger(name='accounts.TwilioGateway')
fake_logger = logging.getLogger(name='accounts.FakeGateway')


class TwilioGateway(object):

    def __init__(self,
                 account_sid=settings.TWILIO_ACCOUNT_SID,
                 auth_token=settings.TWILIO_AUTH_TOKEN,
                 from_phone_number_list=settings.TWILIO_PHONE_NUMBER_LIST):

        self.client = Client(account_sid, auth_token)
        self.from_phone_number_list = from_phone_number_list

    def send_sms(self, to, body):
        try:
            # create and send a message with client
            message = self.client.messages.create(
                to=to,
                from_=random.choice(self.from_phone_number_list),
                body=body)
            uri = 'https://api.twilio.com' + message.uri
            response = self.client.request(method='GET', uri=uri)
            twilio_logger.info("Message sent successfully:{response}".format(
                response=response))

        except TwilioException as e:
            message = e
            twilio_logger.debug(
                'Twilio Message not sent: {error}'.format(error=message.msg))

        return message


class FakeGateway(object):

    def send_sms(self, to, body):
        fake_logger.debug("Message sent to: {phone}. Message: {body}".format(
            phone=to, body=body))
